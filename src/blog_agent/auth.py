import logging
import os

logger = logging.getLogger(__name__)

def authenticate(secret: str) -> bool:
    """Authenticate whether secret is valid or not.
    """
    if not isinstance(secret, str):
        err_msg: str = f"Invalid type: {secret}"
        logger.warning(err_msg)
        return False
    stored_secret: str = os.getenv("SECRET")
    if secret != stored_secret:
        err_msg = f"Mismatch secrets: {secret}"
        logger.warning(err_msg)
        return False
    logger.info("Pass secret")
    return True

