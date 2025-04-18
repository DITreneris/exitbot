"""
Simple deployment script for testing
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a minimal app
app = FastAPI(
    title="ExitBot API",
    description="A minimal deployment test for ExitBot",
    version="1.0.0",
    # Make docs available at root /docs path
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "ExitBot API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/test")
async def test():
    return {"status": "ok", "test": "successful"}

# Run the application
if __name__ == "__main__":
    print("Starting ExitBot deployment test server...")
    print("Access at: http://127.0.0.1:8000")
    print("Documentation: http://127.0.0.1:8000/docs")
    print("Test endpoint: http://127.0.0.1:8000/test")
    print("Health endpoint: http://127.0.0.1:8000/health")
    
    # Use explicit IP binding with restricted host header check
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=8000,
        log_level="info"
    ) 