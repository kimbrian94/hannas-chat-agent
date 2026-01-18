import os
from hannas_agent.config import logging_config
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hannas_agent.rag_service import RAGService

logger = logging_config.get_logger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG service
rag_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG service on startup."""
    global rag_service
    logger.info("Initializing RAG service...")
    rag_service = RAGService()
    rag_service.setup()
    logger.info("RAG service initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down...")

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

def main():
    logger.info("Hello from hannas-agent!")


@app.get("/")
def read_root():
    logger.info("GET / called")
    return {"message": "Welcome to Hanna's Agent!"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat requests using RAG."""
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        # Generate session ID if not provided
        session_id = request.session_id if request.session_id else str(uuid.uuid4())
        
        logger.info(f"Processing chat request for session: {session_id}")
        logger.info(f"User message: {request.message}")
        
        # Get response from RAG service
        response = rag_service.ask(request.message, session_id)
        
        logger.info(f"RAG Agent response: {response}")
        
        return {
            "response": response,
            "session_id": session_id
        }
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-session")
async def clear_session(session_id: str):
    """Clear a specific session's history."""
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        rag_service.clear_session(session_id)
        logger.info(f"Cleared session: {session_id}")
        
        return {"message": "Session cleared successfully"}
    
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    main()
