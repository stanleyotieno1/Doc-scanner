from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from database import init_db

app = FastAPI(title="PDF Extraction Service with Whisperer")

# Configure CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular default port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Database initialized")

# Include API routes
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "PDF Extraction Service",
        "status": "running",
        "endpoints": {
            "extract": "POST /api/extract",
            "get_files": "GET /api/files",
            "get_file": "GET /api/files/{id}",
            "delete_file": "DELETE /api/files/{id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)