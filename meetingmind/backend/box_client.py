# Box API client
import os
from dotenv import load_dotenv

load_dotenv()

def get_box_client():
    """Initialize and return Box client using developer token.

    Box SDK imports are done lazily inside this function so that merely
    importing this module (and `main`) never triggers Box network/auth work.
    """
    from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth

    token = os.getenv("BOX_DEVELOPER_TOKEN")
    if not token:
        raise RuntimeError("BOX_DEVELOPER_TOKEN is not set in the environment")

    auth = BoxDeveloperTokenAuth(token=token)
    return BoxClient(auth=auth)

def search_company_docs(query: str):
    """Simulate Box AI search (demo version)"""
    # In production, this would call Box AI Ask API
    # For demo purposes, returning realistic company context
    return """Based on company documents in Box:

- Q3 2025 ARR reached $6.2M (51% growth QoQ)
- Product roadmap includes fraud detection API v2.0 and developer portal launch in Q1
- Series A raised $15M from Sequoia at $60M pre-money valuation
- Series B planned for Q2 2026 targeting $30M at $200M valuation
- Current team: 18 engineers, hiring 8 more roles (focus on ML team)
- Tech stack: Python, FastAPI, TensorFlow, PostgreSQL, AWS

Documents referenced: product_roadmap_2025.txt, q3_board_update.txt, series_a_term_sheet.txt"""

def create_summary_file(content: str, filename: str):
    """Create a new file in Meeting-Notes folder"""
    client = get_box_client()
    folder_id = os.getenv("MEETING_NOTES_FOLDER_ID")

    from box_sdk_gen import UploadFileAttributes, UploadFileAttributesParentField
    from io import BytesIO
    
    # Convert string to file-like object
    file_stream = BytesIO(content.encode('utf-8'))
    
    uploaded_file = client.uploads.upload_file(
        attributes=UploadFileAttributes(
            name=filename,
            parent=UploadFileAttributesParentField(id=folder_id)
        ),
        file=file_stream
    )
    
    return uploaded_file.entries[0]