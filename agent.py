import os
from dataclasses import dataclass
from typing import Any
from supabase import create_client
import logfire
from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv

load_dotenv()
logfire.configure(send_to_logfire='if-token-present')

@dataclass
class Deps:
    supabase_client: Any

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

seo_agent = Agent(
    model='openai:gpt-4o',
    system_prompt='Generiere einen detaillierten SEO-Bericht einschließlich Meta-Tags und Keywords.',
    deps_type=Deps,
)

async def save_seo_report(ctx: RunContext[Deps], url: str, report_data: dict) -> str:
    """Speichert den SEO-Bericht in der Supabase-Datenbank."""
    report = {
        'url': url,
        'report_data': report_data,
    }
    response = ctx.supabase_client.table('seo_reports').insert(report).execute()
    return response.data[0]['id'] 