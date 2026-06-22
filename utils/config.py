from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

DB_PATH = DATA_DIR / "ai_ceo.db"
CHROMA_DIR = BASE_DIR / "chroma_db"

COMPANY = "BMW"
INDUSTRY = "Automotive / Electric Vehicles"
FOCUS_AREA = "EV strategy and competitive intelligence"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
TOP_K = 5