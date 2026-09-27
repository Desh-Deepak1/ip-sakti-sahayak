from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router

app = FastAPI(
    title="IP-SAKTI Legal Core API",
    description="Backend services for the IP-SAKTI Sahayak",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
        # "https://sahayak-ai-umber.vercel.app/",
        # "http://localhost:3000", 
        # "http://localhost:5173", 
        # "http://127.0.0.1:3000", 
        # "http://127.0.0.1:5173",
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# EXACT MATCH
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"status": "Active"}