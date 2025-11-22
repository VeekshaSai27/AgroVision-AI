import os
from dotenv import load_dotenv


# Load .env file
load_dotenv()


# Resource ID for mandi prices dataset
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"


# Read API key from .env
data_key = os.getenv("DATA_GOV_API_KEY")
DATA_GOV_API_KEY = data_key if data_key else None


# Base URL
DATA_GOV_BASE = "https://api.data.gov.in/resource"