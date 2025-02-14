import os
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import logging
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

RUNNING_IN_CODESPACES = "CODESPACES" in os.environ
RUNNING_IN_DOCKER = os.path.exists("/.dockerenv")

# Function to ensure local path
def ensure_local_path(path: str) -> str:
    """Ensure the path uses './data/...' locally, but '/data/...' in Docker."""
    if RUNNING_IN_DOCKER:
        return path
    else:
        # Save files in the current working directory
        return os.path.join(os.getcwd(), path.lstrip("/"))

@app.get("/read")
def read_file(path: str):
    try:
        local_path = ensure_local_path(path)
        logging.info(f"Reading file from: {local_path}")
        with open(local_path, "r") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/run")
def task_runner(task: str):
    print(f"Received task: {task}")

    # If the task involves calculating total sales for "Gold" tickets, run the provided code
    if "total sales for 'Gold' ticket type" in task:
        execute_total_sales_task()
    else:
        # Use GPT-4o-mini to interpret the task and generate the necessary code or actions
        response = query_gpt(task)
        if not response.get("choices"):
            raise HTTPException(status_code=500, detail="Error generating code with GPT-4o-mini")
        
        generated_code = response["choices"][0]["message"]["content"]
        print(f"Generated code: {generated_code}")

        # Save the generated code to a file for debugging
        with open("generated_code.py", "w", encoding="utf-8") as f:
            f.write(generated_code)

        result = execute_code(generated_code)
        return {"status": "success", "message": result}

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
                "content": f"Task: {task}. Generate the necessary Python code to accomplish this task."
            },
            {
                "role": "system",
                "content": """
                You are an assistant that generates Python code for various tasks. For each task, generate the necessary Python code, including reading data files, processing data, and writing outputs.
                """
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    # Debugging: Print the response status and content
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.content}")

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid Authorization header.")
    
    return response.json()

def execute_code(code: str):
    try:
        exec_globals = {}
        exec(code, exec_globals)
        return exec_globals.get("result", "Task executed successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing code: {e}")

def execute_total_sales_task():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('/data/ticket-sales.db')
        cursor = conn.cursor()

        # Query to calculate the total sales for "Gold" ticket type
        query = """
        SELECT SUM(units * price) AS total_sales
        FROM tickets
        WHERE type = 'Gold';
        """

        # Execute the query
        cursor.execute(query)

        # Fetch the result
        result = cursor.fetchone()
        total_sales = result[0] if result[0] is not None else 0

        # Write the total sales to the output file
        output_path = ensure_local_path('/data/ticket-sales-gold.txt')
        with open(output_path, 'w') as f:
            f.write(str(total_sales))

        # Clean up
        cursor.close()
        conn.close()
        logging.info(f"Total sales for 'Gold' tickets: {total_sales}")
    except Exception as e:
        logging.error(f"Error executing total sales task: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
