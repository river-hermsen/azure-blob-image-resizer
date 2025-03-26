from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    DEBUG = os.getenv("DEBUG", "False") == "True"
