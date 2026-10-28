import os
import json
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("careflow.database")

# Resolve Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "patients.json"

# Database Connection URL
# Detect PostgreSQL URL from environment (Render, Supabase, Neon, AWS RDS)
RAW_DB_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("POSTGRESQL_URL")

def get_engine():
    if RAW_DB_URL:
        # Standardize postgresql:// protocol for SQLAlchemy 2.0
        db_url = RAW_DB_URL.replace("postgres://", "postgresql://")
        try:
            eng = create_engine(db_url, pool_pre_ping=True)
            # Test connection
            with eng.connect() as conn:
                pass
            print(f"[CareFlow DB] Connected to PostgreSQL: {db_url.split('@')[-1] if '@' in db_url else 'configured host'}")
            return eng
        except Exception as e:
            print(f"[CareFlow DB] PostgreSQL connection failed: {e}. Falling back to SQLite.")
    
    # SQLite fallback
    sqlite_path = BASE_DIR / "careflow.db"
    eng = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    print(f"[CareFlow DB] Using persistent SQLite database at: {sqlite_path}")
    return eng

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, default=45)
    gender = Column(String(32), default="Other")
    condition = Column(String(255), default="General Clinical Assessment")
    last_visit = Column(String(64), default=datetime.utcnow().strftime("%Y-%m-%d"))
    next_appointment = Column(String(64), nullable=True)
    medications_json = Column(Text, default="[]")
    lab_results_json = Column(Text, default="{}")
    vitals_json = Column(Text, default="{}")
    missed_followups = Column(Integer, default=0)
    insurance = Column(String(128), default="Standard Clinical Health")
    care_gaps_json = Column(Text, default="[]")
    risk_score = Column(Float, default=0.5)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        def safe_json(val, default):
            if not val:
                return default
            if isinstance(val, (dict, list)):
                return val
            try:
                return json.loads(val)
            except Exception:
                return default

        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "condition": self.condition,
            "last_visit": self.last_visit,
            "next_appointment": self.next_appointment,
            "medications": safe_json(self.medications_json, []),
            "lab_results": safe_json(self.lab_results_json, {}),
            "vitals": safe_json(self.vitals_json, {}),
            "missed_followups": self.missed_followups or 0,
            "insurance": self.insurance or "Standard Clinical Health",
            "care_gaps": safe_json(self.care_gaps_json, []),
            "risk_score": float(self.risk_score or 0.5),
            "notes": self.notes or ""
        }

    @classmethod
    def from_dict(cls, d: dict):
        def to_str(val, default=""):
            if val is None:
                return default
            if isinstance(val, str):
                return val
            return json.dumps(val)

        return cls(
            id=str(d.get("id", "")).strip(),
            name=str(d.get("name", "Unnamed Patient")).strip(),
            age=int(d.get("age", 45)),
            gender=str(d.get("gender", "Other")),
            condition=str(d.get("condition", "General Assessment")),
            last_visit=str(d.get("last_visit") or datetime.utcnow().strftime("%Y-%m-%d")),
            next_appointment=str(d.get("next_appointment")) if d.get("next_appointment") else None,
            medications_json=to_str(d.get("medications", []), "[]"),
            lab_results_json=to_str(d.get("lab_results", {}), "{}"),
            vitals_json=to_str(d.get("vitals", {}), "{}"),
            missed_followups=int(d.get("missed_followups", 0)),
            insurance=str(d.get("insurance", "Standard Clinical Health")),
            care_gaps_json=to_str(d.get("care_gaps", []), "[]"),
            risk_score=float(d.get("risk_score", 0.5)),
            notes=str(d.get("notes", ""))
        )

class ConsultationModel(Base):
    __tablename__ = "consultation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(64), index=True)
    query = Column(Text)
    selected_agent = Column(String(64))
    confidence = Column(Float)
    latency_ms = Column(Float)
    agent_response_json = Column(Text)
    guidelines_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        count = session.query(PatientModel).count()
        if count == 0 and DATA_PATH.exists():
            print("[CareFlow DB] Seeding initial EHR patient roster...")
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                seed_data = json.load(f)
                for item in seed_data:
                    model = PatientModel.from_dict(item)
                    session.merge(model)
            session.commit()
            print(f"[CareFlow DB] Seeded {len(seed_data)} EHR records into database.")
    except Exception as e:
        session.rollback()
        print(f"[CareFlow DB] Seed error: {e}")
    finally:
        session.close()

def db_get_all_patients() -> list[dict]:
    session = SessionLocal()
    try:
        rows = session.query(PatientModel).order_by(PatientModel.id).all()
        return [r.to_dict() for r in rows]
    finally:
        session.close()

def db_get_patient_by_id(patient_id: str) -> dict | None:
    session = SessionLocal()
    try:
        pid = str(patient_id).strip()
        row = session.query(PatientModel).filter(PatientModel.id == pid).first()
        return row.to_dict() if row else None
    finally:
        session.close()

def db_save_patient(patient_dict: dict) -> dict:
    session = SessionLocal()
    try:
        model = PatientModel.from_dict(patient_dict)
        session.merge(model)
        session.commit()
        saved = session.query(PatientModel).filter(PatientModel.id == model.id).first()
        return saved.to_dict() if saved else patient_dict
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def db_delete_patient(patient_id: str) -> bool:
    session = SessionLocal()
    try:
        pid = str(patient_id).strip()
        row = session.query(PatientModel).filter(PatientModel.id == pid).first()
        if row:
            session.delete(row)
            session.commit()
            return True
        return False
    finally:
        session.close()

def db_save_consultation(patient_id: str, query: str, selected_agent: str, confidence: float, latency_ms: float, agent_resp: dict, guidelines: list) -> None:
    session = SessionLocal()
    try:
        entry = ConsultationModel(
            patient_id=str(patient_id),
            query=query,
            selected_agent=selected_agent,
            confidence=float(confidence or 0.9),
            latency_ms=float(latency_ms or 0.0),
            agent_response_json=json.dumps(agent_resp if isinstance(agent_resp, dict) else {"response": str(agent_resp)}),
            guidelines_json=json.dumps(guidelines or [])
        )
        session.add(entry)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[CareFlow DB] Error saving consultation log: {e}")
    finally:
        session.close()

# Auto-initialize on module load
try:
    init_db()
except Exception as e:
    print(f"[CareFlow DB] Initialization notice: {e}")
