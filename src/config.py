# src/config.py
from dotenv import load_dotenv
import os
import openai

def initialize_openai():
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
