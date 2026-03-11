"""
Konfiguration fuer BildungsRadar.
Laedt API-Keys aus der .env Datei.
"""
import os
from dotenv import load_dotenv

# .env Datei laden (enthaelt API-Keys)
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Demo-Modus: Nutzt Beispieldaten statt echte API-Aufrufe
# Auf "false" setzen wenn echte API-Keys vorhanden sind
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Datenbank-Pfad
DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "bildungsradar.db"
)

# OpenAI Einstellungen
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
