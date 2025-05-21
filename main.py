# HINWEIS: Diese Datei ist für lokale Entwicklung gedacht.
# Für Vercel-Deployment muss die App in api/main.py liegen!

from fastapi import FastAPI
from pydantic import BaseModel
from agent import Deps, supabase_client, seo_agent
from agent_tools import generate_seo_report, send_report_email
from pydantic_ai import RunContext
import asyncio
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS für Entwicklung und Produktion
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "https://analyzer.growing-brands.de"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SEORequest(BaseModel):
    url: str

class SendReportRequest(BaseModel):
    report_id: str
    to: str

class DeleteSeoReportRequest(BaseModel):
    report_id: str

@app.post("/seo-report")
async def seo_report(request: SEORequest):
    ctx = Deps(supabase_client=supabase_client)
    result = await generate_seo_report(ctx, request.url)
    return result

@app.post("/send-seo-report")
async def send_seo_report_api(request: SendReportRequest):
    from supabase import create_client
    import os
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase = create_client(supabase_url, supabase_key)
    res = supabase.table('seo_reports').select('*').eq('id', request.report_id).execute()
    if not res.data or not res.data[0].get('report_data'):
        return {"error": "Bericht nicht gefunden"}
    gpt_report = res.data[0]['report_data'].get('gpt_report', '')
    url = res.data[0].get('url', '')
    await send_report_email(gpt_report, request.to, url)
    return {"status": "sent"}

@app.post("/delete-seo-report")
async def delete_seo_report(request: DeleteSeoReportRequest):
    from supabase import create_client
    import os
    import uuid
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase = create_client(supabase_url, supabase_key)
    try:
        # Prüfe, ob die ID eine gültige UUID ist
        try:
            uuid.UUID(request.report_id)
        except Exception:
            return JSONResponse(status_code=400, content={"error": "Ungültige Bericht-ID"})
        res = supabase.table('seo_reports').delete().eq('id', request.report_id).execute()
        if res.data and len(res.data) > 0:
            return {"status": "deleted"}
        else:
            return JSONResponse(status_code=404, content={"error": "Bericht nicht gefunden"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)}) 