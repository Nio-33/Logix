"""
Firebase Configuration and Initialization
"""

import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud import logging as cloud_logging

logger = logging.getLogger(__name__)


def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials
    """
    try:
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            logger.info("Firebase already initialized")
            return firebase_admin.get_app()

        # Get credentials path from environment
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        # Skip Firebase in development if no credentials provided
        if os.getenv("ENVIRONMENT") == "development" and not cred_path:
            logger.warning(
                "Firebase skipped in development mode - no credentials provided"
            )
            return None

        if cred_path and os.path.exists(cred_path):
            # Initialize with service account file
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(
                cred, {"projectId": os.getenv("FIREBASE_PROJECT_ID")}
            )
            logger.info("Firebase initialized with service account credentials")
        else:
            # Initialize with default credentials (for Cloud Run)
            firebase_admin.initialize_app()
            logger.info("Firebase initialized with default credentials")

        # Initialize Cloud Logging
        if os.getenv("ENVIRONMENT") == "production":
            cloud_logging_client = cloud_logging.Client()
            cloud_logging_client.setup_logging()

        return firebase_admin.get_app()

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def get_firestore_client():
    """
    Get Firestore client instance
    """
    try:
        # Check if Firebase is initialized
        if not firebase_admin._apps:
            logger.warning("Firestore client not available - Firebase not initialized")
            return None

        return firestore.client()
    except Exception as e:
        logger.error(f"Failed to get Firestore client: {e}")
        return None


def get_auth_client():
    """
    Get Firebase Auth client instance
    """
    try:
        return auth
    except Exception as e:
        logger.error(f"Failed to get Auth client: {e}")
        raise
