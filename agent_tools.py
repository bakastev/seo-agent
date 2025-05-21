import httpx
from bs4 import BeautifulSoup
from agent import save_seo_report, Deps
from pydantic_ai import RunContext
import os
import markdown2

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@growing-brands.de")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_DOMAIN = "review.growing-brands.de"

async def scrape_website(ctx: RunContext[Deps], url: str) -> dict:
    print(f"[SEO-AGENT] Starte Crawl für: {url}")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Meta-Tags
        meta_tags = {meta.get('name', meta.get('property', '')): meta.get('content', '') for meta in soup.find_all('meta')}
        # Canonical
        canonical = soup.find('link', rel='canonical')
        # Robots
        robots = meta_tags.get('robots', '')
        # OpenGraph
        og_tags = {meta.get('property', ''): meta.get('content', '') for meta in soup.find_all('meta') if meta.get('property', '').startswith('og:')}
        # Twitter
        twitter_tags = {meta.get('name', ''): meta.get('content', '') for meta in soup.find_all('meta') if meta.get('name', '').startswith('twitter:')}
        # Headings
        headings = {f"h{i}": [h.text.strip() for h in soup.find_all(f"h{i}")] for i in range(1, 7)}
        # Bilder
        images = [{
            'src': img.get('src'),
            'alt': img.get('alt', ''),
            'title': img.get('title', '')
        } for img in soup.find_all('img')]
        # Links
        links = [{
            'href': a.get('href'),
            'text': a.text.strip(),
            'rel': a.get('rel', '')
        } for a in soup.find_all('a')]
        # Sitemap & robots.txt
        sitemap_url = None
        robots_txt = None
        for link in soup.find_all('link', rel=True):
            if link.get('rel') == ['sitemap']:
                sitemap_url = link.get('href')
        # robots.txt separat abrufen
        try:
            robots_url = url.rstrip('/') + '/robots.txt'
            robots_resp = await client.get(robots_url)
            if robots_resp.status_code == 200:
                robots_txt = robots_resp.text
        except Exception:
            robots_txt = None
        seo_data = {
            'title': soup.title.string if soup.title else '',
            'meta_description': meta_tags.get('description', ''),
            'meta_tags': meta_tags,
            'canonical': canonical.get('href') if canonical else '',
            'robots': robots,
            'og_tags': og_tags,
            'twitter_tags': twitter_tags,
            'headings': headings,
            'images': images,
            'links': links,
            'sitemap_url': sitemap_url,
            'robots_txt': robots_txt,
            'raw_html': response.text
        }
        print(f"[SEO-AGENT] SEO-Daten extrahiert: {seo_data}")
        return seo_data

async def gpt_seo_report(ctx: RunContext[Deps], url: str, seo_data: dict) -> str:
    from openai import AsyncOpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("[SEO-AGENT] FEHLER: OPENAI_API_KEY fehlt!")
        raise Exception("OPENAI_API_KEY fehlt!")
    client = AsyncOpenAI(api_key=openai_api_key)
    prompt = f"""
Du bist ein professioneller SEO-Experte. Analysiere die folgende Website umfassend und liefere einen strukturierten Bericht mit:
- Meta-Tags (Title, Description, Robots)
- Überschriftenstruktur (H1, H2, H3)
- Keyword-Analyse (Häufigkeit, Relevanz)
- Mobile Optimierung
- Interne/Externe Links
- Technische SEO (Indexierung, Canonical, Sitemap, Robots.txt)
- Content-Qualität
- Backlinks (falls erkennbar)
- Social Signals (falls erkennbar)
- Konkrete, priorisierte Verbesserungsvorschläge für jede Kategorie
Nutze klare Überschriften und nummerierte Listen. Am Ende: Zusammenfassung und Top-5 Sofortmaßnahmen.

URL: {url}

Meta Title: {seo_data.get('title')}
Meta Description: {seo_data.get('meta_description')}
H1: {seo_data.get('h1')}
Keywords: {', '.join(seo_data.get('keywords', []))}

HTML-Auszug:
{seo_data.get('raw_html')[:2000]}
"""
    print("[SEO-AGENT] Sende Prompt an OpenAI...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2,
            max_tokens=1800
        )
        print("[SEO-AGENT] GPT-Report erhalten.")
        return response.choices[0].message.content
    except Exception as e:
        print(f"[SEO-AGENT] FEHLER bei OpenAI: {e}")
        raise Exception(f"OpenAI-Fehler: {e}")

def build_email_html(subject: str, markdown_content: str, url: str) -> str:
    html_content = markdown2.markdown(markdown_content)
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; background: #f9fafb; color: #222; }}
            .container {{ max-width: 600px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 32px; }}
            h1, h2, h3 {{ color: #10B981; }}
            a {{ color: #10B981; }}
            .footer {{ color: #888; font-size: 13px; margin-top: 32px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SEO-Analysebericht</h1>
            <p style="color:#6B7280;">für <a href="{url}">{url}</a></p>
            {html_content}
            <div class="footer">
                <p>Automatisch erstellt von <a href="https://growing-brands.de">Growing Brands SEO Agent</a></p>
            </div>
        </div>
    </body>
    </html>
    '''

async def send_report_email(report_markdown: str, to_email: str, url: str = ""):
    if not RESEND_API_KEY:
        print("[SEO-AGENT] FEHLER: RESEND_API_KEY fehlt!")
        raise Exception("RESEND_API_KEY fehlt!")
    print(f"[SEO-AGENT] Sende Bericht an {to_email}...")
    subject = "Ihr ausführlicher SEO-Bericht"
    html = build_email_html(subject, report_markdown, url)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"SEO Agent <report@{RESEND_DOMAIN}>",
                "to": [to_email],
                "subject": subject,
                "html": html
            }
        )
        print(f"[SEO-AGENT] Resend-Response: {resp.status_code} {resp.text}")
        if resp.status_code >= 400:
            raise Exception(f"Resend-Fehler: {resp.text}")

async def generate_seo_report(ctx: RunContext[Deps], url: str) -> dict:
    try:
        seo_data = await scrape_website(ctx, url)
        gpt_report = await gpt_seo_report(ctx, url, seo_data)
        print("[SEO-AGENT] Speichere Bericht in Supabase...")
        report_id = await save_seo_report(ctx, url, {"seo_data": seo_data, "gpt_report": gpt_report})
        print(f"[SEO-AGENT] Bericht gespeichert mit ID: {report_id}")
        await send_report_email(gpt_report, ADMIN_EMAIL, url)
        print("[SEO-AGENT] Bericht an Admin gesendet.")
        return {"report_id": report_id, "seo_data": seo_data, "gpt_report": gpt_report}
    except Exception as e:
        print(f"[SEO-AGENT] Fehler: {e}")
        return {"error": str(e)} 