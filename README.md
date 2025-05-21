# SEO-Agent Backend

## Hinweise für Vercel-Deployment
- Die FastAPI-App muss in `api/main.py` liegen.
- Die Datei `requirements.txt` muss mindestens `fastapi` und `uvicorn` enthalten.
- Siehe auch die Datei `vercel.json` für die Routing-Konfiguration.

## Setup

1. Erstelle eine `.env`-Datei basierend auf `.env.example` und trage deine Supabase- und OpenAI-Keys ein.
2. Installiere die Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```
3. Starte das Backend:
   ```bash
   uvicorn main:app --reload
   ```

## API

POST `/seo-report`
```json
{
  "url": "https://example.com"
}
```
Antwort:
```json
{
  "report_id": "...",
  "data": { ...SEO-Daten... }
}
```

## Vercel Deployment Quickstart

1. Lege einen Ordner `api` an und verschiebe deine FastAPI-App nach `api/main.py`.
2. Erstelle eine `vercel.json` im Root:

```json
{
  "version": 2,
  "builds": [
    { "src": "api/main.py", "use": "@vercel/python", "config": { "maxLambdaSize": "50mb" } }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "api/main.py" }
  ]
}
```
3. Passe die `requirements.txt` an (mindestens fastapi und uvicorn).
4. Committe und pushe alles nach GitHub.
5. Vercel baut und deployed automatisch. 