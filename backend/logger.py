import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def log_request(endpoint: str, data: dict = None):
    logger.info(f"REQUEST {endpoint}: {data}")

def log_response(endpoint: str, response: dict):
    logger.info(f"RESPONSE {endpoint}: {response}")

def log_resume_data(data: dict):
    logger.info(f"EXTRACTED RESUME DATA: {data}")

def log_form_fields(fields: dict):
    logger.info(f"FORM FIELDS DETECTED: {fields}")

def log_error(error: str, context: str = ""):
    logger.error(f"ERROR {context}: {error}")