import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URI = os.getenv("DATABASE_URI")
    PORT = os.getenv("PORT", 8000)