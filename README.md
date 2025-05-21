# SEO-Agent Backend

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