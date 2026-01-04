import os

import logging
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI, APITimeoutError, OpenAIError
from pydantic import BaseModel

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

sessions = {}

class DetailedParam(BaseModel):
    prompt: dict

class Action(BaseModel):
    params: dict
    detailedParams: dict

class RequestBody(BaseModel):
    action: Action

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
    logger.info(f"POST /chat called with: {request}")
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = []
    
    agent_response = get_agent_response(request.message, sessions[session_id])

    sessions[session_id].append({"role": "user", "content": request.message})
    sessions[session_id].append({"role": "assistant", "content": agent_response})

    logger.info("Current session history:")
    log_sessions()

    return {
        "response": agent_response, 
        "session_id": session_id
    }
    

def get_agent_response(message: str, session_history: list = None) -> str:
    """
    External function to call OpenAI API and get response.
    """
    try:
        messages = [
            {
                "role": "system",
                "content": "You are Hanna's Mom's Care AI Assistant. Answer in a helpful and friendly manner."
            }
        ]
        
        # Add session history if available
        if session_history:
            messages.extend(session_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": message
        })
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        
        return response.choices[0].message.content
        
    except APITimeoutError:
        logger.error("OpenAI API timeout")
        return "Sorry, the request timed out. Please try again."
    except OpenAIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        return f"An error occurred: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "An unexpected error occurred."

def log_sessions():
    for session_id, history in sessions.items():
        logger.info(f"Session ID: {session_id}")
        for message in history:
            logger.info(f"{message['role']}: {message['content']}")


if __name__ == "__main__":
    main()
