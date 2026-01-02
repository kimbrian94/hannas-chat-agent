import os

import logging
from fastapi import FastAPI
from openai import OpenAI, APITimeoutError, OpenAIError
from pydantic import BaseModel


# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DetailedParam(BaseModel):
    prompt: dict

class Action(BaseModel):
    params: dict
    detailedParams: dict

class RequestBody(BaseModel):
    action: Action

def main():
    logger.info("Hello from hannas-agent!")


@app.get("/")
def read_root():
    logger.info("GET / called")
    return {"message": "Welcome to Hanna's Agent!"}


@app.post("/generate")
async def generate_text(request: RequestBody):
    logger.info(f"POST /generate called with: {request}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": request.action.params['prompt']
                }
            ]
        )
        logger.info("OpenAI response received successfully.")
        return {
            "version": "1.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": response.choices[0].message.content
                        }
                    }
                ]
            }
        }
    except APITimeOutError:
        logger.error("The request timed out.")
        return {"error": "The request timed out. Please try again later."}
    except OpenAIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        return {"error": f"An OpenAI error occurred: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}



if __name__ == "__main__":
    main()
