import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")
    
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in .env file")
