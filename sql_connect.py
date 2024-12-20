import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from model import Base
load_dotenv()

DATABASE_URL = (f"mysql+mysqlconnector"
                f"://{os.getenv('DATABASE_USER')}"
                f":{os.getenv('DATABASE_PASSWORD')}"
                f"@{os.getenv('DATABASE_HOST')}"
                f":{os.getenv('DATABASE_PORT')}"
                f"/{os.getenv('DATABASE_NAME')}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
try:
    with engine.connect() as connection:
        print("Kết nối thành công!")
except Exception as e:
    print("Kết nối thất bại:", e)

# Dependency để lấy session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
