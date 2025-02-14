# script
# requires-python = ">=3.13"
# dependencies = [
#     "fastapi",
#     "uvicorn",
#     "requests",
#     "pandas",
#     "pillow",
#     "httpx",
#     "python-dotenv"
# ]

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import uvicorn
from dotenv import load_dotenv
import subprocess
import json
import sqlite3
import pandas as pd
from PIL import Image
import httpx
import base64
import numpy as np
import re
from pathlib import Path
import glob
from dateutil.parser import parse

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

RUNNING_IN_CODESPACES = "CODESPACES" in os.environ
RUNNING_IN_DOCKER = os.path.exists("/.dockerenv")

def ensure_local_path(path: str) -> str:
    """Ensure the path uses './data/...' locally, but '/data/...' in Docker."""
    if ((not RUNNING_IN_CODESPACES) and RUNNING_IN_DOCKER): 
        return path
    else:
        return path.lstrip("/")  # If absolute local path, remove leading slash

@app.get("/read")
def read_file(path: str):
    try:
        with open(path, "r") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/run")
def task_runner(task: str):
    print(f"Received task: {task}")

    # Use GPT-4o-mini to interpret the task and generate the necessary code or actions
    response = query_gpt(task)
    tool_calls = response.get("choices", [])[0].get("message", {}).get("tool_calls", [])

    for tool_call in tool_calls:
        if tool_call["type"] == "function" and tool_call["function"]["name"] == "script_runner":
            script_runner(json.loads(tool_call["function"]["arguments"]))
        elif tool_call["type"] == "function" and tool_call["function"]["name"] == "format_markdown":
            format_markdown()

    return {"status": "success", "message": "Task executed"}

def format_markdown():
    try:
        subprocess.run(["npx", "prettier@3.4.2", "--write", "/data/format.md"], check=True)
        return {"message": "Markdown formatted successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error formatting markdown: {e}")


def query_gpt(task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": task
            },
            {
                "role": "system",
                "content": """
                You are an assistant who has to do a variety of tasks. 
                If the task involves running a script, you should use the script_runner tool.
                The script_runner tool requires a script URL and a list of arguments.
                Construct the script URL based on the task description and pass the necessary arguments.
                """
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "script_runner",
                    "description": "Install a package and run a script from a URL with provided arguments.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "script_url": {
                                "type": "string",
                                "description": "The URL of the script to run."
                            },
                            "args": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of arguments to pass to the script"
                            }
                        },
                        "required": ["script_url", "args"]
                    }
                }
            }
        ],
        "tool_choice": "auto"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    # Debugging: Print the response status and content
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.content}")

    return response.json()

def script_runner(arguments):
    script_url = arguments["script_url"]
    args = arguments["args"]

    # Download the script
    response = requests.get(script_url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail=f"Script not found at {script_url}")
    
    script_content = response.text

    # Save the script to a temporary file
    script_path = "temp_script.py"
    with open(script_path, "w", encoding="utf-8") as script_file:
        script_file.write(script_content)

    try:
        # Ensure dependencies are installed
        subprocess.run(["pip", "install", "faker", "pillow"], check=True)

        # Validate the script content
        subprocess.run(["python", "-m", "py_compile", script_path], check=True)
        
        # Run the script with the provided arguments
        subprocess.run(["python", script_path] + args, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Script execution failed: {e}")
    finally:
        # Clean up the temporary script file
        os.remove(script_path)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
