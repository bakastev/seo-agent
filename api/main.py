from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "SEO Agent Backend läuft!"} 