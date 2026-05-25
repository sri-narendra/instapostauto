"""Runtime configuration for the carousel engine."""

import os

from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

WIDTH = 1080
HEIGHT = 1350
OUTPUT_DIR = "output"
