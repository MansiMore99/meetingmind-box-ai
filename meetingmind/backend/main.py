from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from box_client import search_company_docs, create_summary_file
from datetime import datetime
import os

app = FastAPI()

# Enable CORS so frontend can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptRequest(BaseModel):
    transcript: str

@app.get("/")
def root():
    return {"status": "MeetingMind API is running"}

def extract_decisions_and_actions(transcript: str) -> dict:
    import urllib.request
    import json as jsonlib
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    prompt = """Analyze this meeting transcript. Extract:
1. KEY DECISIONS (what was decided, max 4 bullet points)
2. ACTION ITEMS (who does what by when, max 4 bullet points)

Format exactly like this, no extra text:
DECISIONS:
- Decision 1
- Decision 2

ACTIONS:
- [Owner] Action by [deadline]
- [Owner] Action by [deadline]

TRANSCRIPT:
""" + transcript[:2000]

    payload = jsonlib.dumps({
        "model": "claude-haiku-4-5",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = jsonlib.loads(resp.read().decode('utf-8'))
            text = result['content'][0]['text']
            
            decisions = ""
            actions = ""
            
            if "DECISIONS:" in text and "ACTIONS:" in text:
                parts = text.split("ACTIONS:")
                decisions = parts[0].replace("DECISIONS:", "").strip()
                actions = parts[1].strip()
            else:
                decisions = "- See full transcript for decisions"
                actions = "- See full transcript for action items"
            
            return {"decisions": decisions, "actions": actions}
    except Exception as e:
        return {
            "decisions": "- Could not extract decisions",
            "actions": "- Could not extract action items"
        }
@app.post("/process-meeting")
def process_meeting(request: TranscriptRequest):
    try:
        transcript = request.transcript
        
        # Step 1: Use Box AI to search company docs for relevant context
        search_query = f"Based on this meeting transcript, what relevant company information exists?\n\n{transcript[:500]}"
        ai_context = search_company_docs(search_query)
        
        # Step 2: Extract decisions and action items using Claude
        extracted = extract_decisions_and_actions(transcript)

        # Step 3: Generate structured summary
        summary = f"""MEETING SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

TRANSCRIPT EXCERPT:
{transcript[:300]}...

RELEVANT COMPANY CONTEXT (from Box AI):
{ai_context}

KEY DECISIONS:
{extracted['decisions']}

ACTION ITEMS:
{extracted['actions']}

RELATED DOCUMENTS:
- Located in Company-Docs folder
- See Box AI context above for specific references
"""
        
        # Step 3: Create file in Box
        filename = f"meeting_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        uploaded_file = create_summary_file(summary, filename)
        
        return {
            "success": True,
            "summary": summary,
            "file_id": uploaded_file.id,
            "file_name": uploaded_file.name,
            "box_url": f"https://app.box.com/file/{uploaded_file.id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/folder-structure")
def get_folder_structure():
    try:
        from box_client import get_box_client
        client = get_box_client()
        
        company_docs_id = os.getenv("COMPANY_DOCS_FOLDER_ID")
        meeting_notes_id = os.getenv("MEETING_NOTES_FOLDER_ID")
        investor_relations_id = os.getenv("INVESTOR_RELATIONS_FOLDER_ID")
        
        # Get file counts for each folder
        company_docs = client.folders.get_folder_items(folder_id=company_docs_id)
        meeting_notes = client.folders.get_folder_items(folder_id=meeting_notes_id)
        investor_relations = client.folders.get_folder_items(folder_id=investor_relations_id)
        
        return {
            "success": True,
            "folders": {
                "company_docs": {
                    "id": company_docs_id,
                    "name": "Company-Docs",
                    "file_count": len([item for item in company_docs.entries if item.type == "file"]),
                    "url": f"https://app.box.com/folder/{company_docs_id}"
                },
                "meeting_notes": {
                    "id": meeting_notes_id,
                    "name": "Meeting-Notes",
                    "file_count": len([item for item in meeting_notes.entries if item.type == "file"]),
                    "url": f"https://app.box.com/folder/{meeting_notes_id}"
                },
                "investor_relations": {
                    "id": investor_relations_id,
                    "name": "Investor-Relations",
                    "file_count": len([item for item in investor_relations.entries if item.type == "file"]),
                    "url": f"https://app.box.com/folder/{investor_relations_id}"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))