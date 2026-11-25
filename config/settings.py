"""All app settings live here, so you change them in one place."""

import os

from dotenv import load_dotenv

# load_dotenv() reads the file ".env" (if it exists) and puts each line
# into the computer's environment variables. The key never appears in our code.
load_dotenv()

APP_TITLE = "HEOR Data Analysis Assistant"

# Biggest CSV we accept, in megabytes. Keeps the app fast on a laptop.
MAX_FILE_SIZE_MB = 20

# How many rows to show on the Preview page by default.
PREVIEW_ROWS = 10

# ---- LLM settings (Phase 3) ----
# The secret key comes from .env. If it is missing we get None (no crash here).
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Which Groq model to use. gpt-oss-120b supports tool calling.
# You can change the model in .env without touching code.
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")