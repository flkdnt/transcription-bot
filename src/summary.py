import json
import logging
import os
import re
from datetime import datetime

from langchain_ollama import ChatOllama
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    # --- LLM Configuration ---
