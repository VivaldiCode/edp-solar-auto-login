import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from appv2 import run_browser_flow
# Variáveis globais
CLIENT_ID = os.environ.get("CLIENT_ID")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "edpc://solar")
AUTH_HOST = os.environ.get("AUTH_HOST", "prd-accountlinking.auth.eu-west-1.amazoncognito.com")

app = FastAPI(title="EDP Solar Auth API")

# Schema para request
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginRequest):
    try:
        tokens = run_browser_flow(data.username, data.password)
        return tokens
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
