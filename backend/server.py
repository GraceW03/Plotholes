# backend/server.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from model import analyze_image

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze(request: Request):
    body = await request.json()
    image_url = body.get("image_url")
    if not image_url:
        return JSONResponse({"error": "Missing image_url"}, status_code=400)

    result = analyze_image(image_url)
    return JSONResponse(result)
