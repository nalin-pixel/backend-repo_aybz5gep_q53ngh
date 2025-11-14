import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Literal, Optional

from database import create_document
from schemas import ContactMessage

app = FastAPI(title="Leonardo Notargiacomo Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Portfolio Backend Running"}

@app.get("/api/metrics")
def get_metrics():
    return {
        "experience_years": 2,
        "production_apps": 3,
        "ad_spend_managed": 6000,
        "best_roas": 3.6,
        "projects": [
            {"name": "SkyVoyage", "type": "IT"},
            {"name": "Detiabc.ru", "type": "IT"},
            {"name": "Soorpriz", "type": "Marketing"},
            {"name": "Dobrosvit", "type": "Marketing"}
        ]
    }

# Marketing case studies static dataset with filter categories
class CaseStudy(BaseModel):
    title: str
    category: Literal["E-commerce", "Lead Gen", "Local Business", "All"]
    metric_label: str
    metric_value: str
    budget: Optional[str] = None
    summary: str

CASE_STUDIES: List[CaseStudy] = [
    CaseStudy(
        title="Soorpriz",
        category="E-commerce",
        metric_label="Best ROAS",
        metric_value="3.6x",
        budget="$5.5K",
        summary="Scaled ROAS while testing creatives and audience stacks"
    ),
    CaseStudy(
        title="Dobrosvit",
        category="Lead Gen",
        metric_label="Cost per Lead",
        metric_value="€7",
        budget=None,
        summary="Generated 70 qualified leads via conversion-optimized funnels"
    ),
    CaseStudy(
        title="Fertility Therapy",
        category="Lead Gen",
        metric_label="CPL",
        metric_value="€18.75",
        budget=None,
        summary="Delivered 8 booked calls through targeted lead gen campaigns"
    ),
]

@app.get("/api/case-studies")
def list_case_studies(category: Optional[str] = None):
    if not category or category.lower() == "all":
        return [cs.model_dump() for cs in CASE_STUDIES]
    filtered = [cs.model_dump() for cs in CASE_STUDIES if cs.category.lower() == category.lower()]
    return filtered

class ContactIn(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    source: Optional[str] = None

@app.post("/api/contact")
def submit_contact(payload: ContactIn):
    try:
        # Persist to DB using schemas.ContactMessage validation
        doc = ContactMessage(**payload.model_dump())
        inserted_id = create_document("contactmessage", doc)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
