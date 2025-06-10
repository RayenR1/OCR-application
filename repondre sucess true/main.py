from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/send-message")
async def options_send_message():
    return JSONResponse(status_code=200, content={"success": True , "message": "Test response"})

@app.post("/send-message")
async def send_message():
    # Temporairement, retourner une réponse simple pour tester
    return {"success": True, "message": "Test response"}