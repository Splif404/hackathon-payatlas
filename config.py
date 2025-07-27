import os
from dotenv import load_dotenv


load_dotenv()


DIRECTUS_URL = os.getenv("DIRECTUS_URL", "https://directus.corefy.org")


API_TOKEN = os.getenv("API_TOKEN", "your-api-token-here")


COLLECTION_NAME = os.getenv("COLLECTION_NAME", "hakaton_NAZVA_KOMANDI")


REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "300"))  # 5 minutes
