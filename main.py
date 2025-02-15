# /// script

# dependencies = [
#     "requests",
#     "fastapi",
#     "uvicorn",
#     "python-dateutil",
#     "pandas",
#     "db-sqlite3",
#     "scipy",
#     "pybase64",
#     "python-dotenv",
#     "httpx",
#     "markdown",
#     "duckdb",
#     "beautifulsoup4",
#     "pillow",
#     "git",
# ]
# ///

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re
import httpx
import json
from tasks import (
    A1, A2, A3, A4, A5, A6, A7, A8, A9, A10,
    B3, B4, B5, B6, B7, B8, B9, B10
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

load_dotenv()

openai_api_chat = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"  # for testing
openai_api_key = os.getenv("AIPROXY_TOKEN")

if not openai_api_key:
    raise ValueError("AIPROXY_TOKEN not found in environment variables or .env file.")

headers = {
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json",
}

function_definitions_llm = [
    {
        "name": "A1",
        "description": """
            Runs the `datagen.py` script to generate data files needed for other tasks. 
            Specify the email address to use as an argument to the script. 
            It is crucial to run this function FIRST to create the necessary data files.
            Make sure the function returns an HTTP 200 response.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "pattern": r"[\w\.-]+@[\w\.-]+\.\w+",
                    "description": "The email address to pass as an argument to `datagen.py`. Do not change this."
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "A2",
        "description": """
            Formats a Markdown file using `prettier`. 
            Make sure to provide the correct `prettier_version` and `filename`. 
            This function modifies the file in-place. The goal of this file is to format the file.
            Make sure the function returns an HTTP 200 response.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "prettier_version": {
                    "type": "string",
                    "pattern": r"prettier@\d+\.\d+\.\d+",
                    "description": "The version of prettier to use (e.g., `prettier@3.4.2`). Do not make any mistake when using this function"
                },
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.md)",
                    "description": "The path to the Markdown file to format. Be sure that path is well-formed and valid."
                }
            },
            "required": ["plaintext", "filename"]
        }
    },
    {
        "name": "A3",
        "description": """
            Counts the number of occurrences of a specific weekday in a date file. 
            The `filename` should be a text file with dates, one date per line. 
            Dates may be in various formats. Use the `dateutil` library to parse the dates. 
            The `weekday` parameter should be the target weekday (e.g., Monday, Tuesday).
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r"/data/.*dates.*\.txt",
                    "description": "Path to the dates file. Dates may be in various formats. All file should start with the data tag. The filename file should also end with the file tag .txt"
                },
                "targetfile": {
                    "type": "string",
                    "pattern": r"/data/.*/(.*\.txt)",
                    "description": "Path to the file where the count will be written.  All file should start with the data tag.The targetfile should also end with the file tag .txt"
                },
                "weekday": {
                    "type": "integer",
                    "pattern": r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
                    "description": "The target weekday to count. Do not deviate"
                }
            },
            "required": ["filename", "targetfile", "weekday"]
        }
    },
    {
        "name": "A4",
        "description": """
            Sorts a JSON contacts file by `last_name` and then `first_name`. 
            The `filename` should be a JSON file containing an array of contact objects. 
            The sorted data is saved to the `targetfile`. The name of the file must end with the .json tag.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.json)",
                    "description": "Path to the JSON contacts file.Make sure you include .json"
                },
                "targetfile": {
                    "type": "string",
                    "pattern": r".*/(.*\.json)",
                    "description": "Path to save the sorted JSON data.Make sure you include .json"
                }
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "A5",
        "description": """
            Retrieves the first line of the N most recent `.log` files from a directory and saves them to an output file.
            Specify `log_dir_path`, `output_file_path`, and `num_files`. The `num_files` is the most recent files that the bot should be taking from.Make sure that all files are saved into a txt output file.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "log_dir_path": {
                    "type": "string",
                    "pattern": r".*/logs",
                    "default": "/data/logs",
                    "description": "Path to the directory containing the log files. Please ensure that the path log_dir_path, is the correct file, and ends with the log tag."
                },
                "output_file_path": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/logs-recent.txt",
                    "description": "Path to save the combined log entries.Make sure you include .txt"
                },
                "num_files": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 10,
                    "description": "Number of recent log files to process. This is an integer."
                }
            },
            "required": ["log_dir_path", "output_file_path", "num_files"]
        }
    },
    {
        "name": "A6",
        "description": """
            Generates an index of Markdown files from a directory and saves it as a JSON file.
            The index maps each filename (without the `/data/docs/` prefix) to its first H1 heading.Be sure that doc and output are .json as well.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "doc_dir_path": {
                    "type": "string",
                    "pattern": r".*/docs",
                    "default": "/data/docs",
                    "description": "Path to the directory containing the Markdown files. Make sure you include .md"
                },
                "output_file_path": {
                    "type": "string",
                    "pattern": r".*/(.*\.json)",
                    "default": "/data/docs/index.json",
                    "description": "Path to save the JSON index file.Make sure you include .json"
                }
            },
            "required": ["doc_dir_path", "output_file_path"]
        }
    },
    {
        "name": "A7",
        "description": """
            Extracts the sender's email address from a text file and saves it to an output file.
            The `filename` should be a text file containing an email message.Make sure that all files are saved into a txt output file.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/email.txt",
                    "description": "Path to the text file containing the email message. Be sure to include.txt"
                },
                "output_file": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/email-sender.txt",
                    "description": "Path to save the extracted email address. Be sure to include.txt"
                }
            },
            "required": ["filename", "output_file"]
        }
    },
    {
        "name": "A8",
        "description": """
            Extracts the credit card number from an image, validates it, and writes it to a file.
            The `image_path` should be a path to the image with the credit card number. The output tag is credit_card
            This function requires the AIPROXY_TOKEN to be set.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/credit_card.txt",
                    "description": "Path to save the extracted credit card number. Must be credit_card"
                },
                "image_path": {
                    "type": "string",
                    "pattern": r".*/(.*\.png)",
                    "default": "/data/credit_card.png",
                    "description": "Path to the image containing the credit card number. The filename is credit_card"
                }
            },
            "required": ["filename", "image_path"]
        }
    },
    {
        "name": "A9",
        "description": """
            Finds the most similar pair of comments from a text file using embeddings and saves them to an output file.
            This function requires the AIPROXY_TOKEN to be set.The name must be comment.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/comments.txt",
                    "description": "Path to the text file containing the comments. Must be comments"
                },
                "output_filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/comments-similar.txt",
                    "description": "Path to save the most similar pair of comments. Must be comment similar"
                }
            },
            "required": ["filename", "output_filename"]
        }
    },
    {
        "name": "A10",
        "description": """
            Identifies high-value (gold) ticket sales from a database and saves the total sales to a text file.
            The `filename` should be a path to a SQLite database file with a `tickets` table. the name of the file must be ticket
            Specify the SQL `query` to retrieve the total sales for the "Gold" ticket type.The name must be ticket
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.db)",
                    "default": "/data/ticket-sales.db",
                    "description": "Path to the SQLite database file. The name of the file must be ticket"
                },
                "output_filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/ticket-sales-gold.txt",
                    "description": "Path to save the total gold ticket sales. The name of the file must be ticket"
                },
                "query": {
                    "type": "string",
                    "pattern": "SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'",
                    "description": "SQL query to retrieve total gold ticket sales. Leave this as the same."
                }
            },
            "required": ["filename", "output_filename", "query"]
        }
    },
    {
        "name": "B3",
        "description": "Download content from a URL and save it to the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "pattern": r"https?://.*",
                    "description": "URL to download content from."
                },
                "save_path": {
                    "type": "string",
                    "pattern": r".*/.*",
                    "description": "Path to save the downloaded content."
                }
            },
            "required": ["url", "save_path"]
        }
    },
    {
        "name": "B5",
        "description": "Execute a SQL query on a specified database file and save the result to an output file.",
        "parameters": {
            "type": "object",
            "properties": {
                "db_path": {
                    "type": "string",
                    "pattern": r".*/(.*\.db)",
                    "description": "Path to the SQLite database file."
                },
                "query": {
                    "type": "string",
                    "description": "SQL query to be executed on the database."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "description": "Path to the file where the query result will be saved."
                }
            },
            "required": ["db_path", "query", "output_filename"]
        }
    },
    {
        "name": "B6",
        "description": "Fetch content from a URL and save it to the specified output file.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "pattern": r"https?://.*",
                    "description": "URL to fetch content from."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": r".*/.*",
                    "description": "Path to the file where the content will be saved."
                }
            },
            "required": ["url", "output_filename"]
        }
    },
    {
        "name": "B7",
        "description": "Process an image by optionally resizing it and saving the result to an output path.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "pattern": r".*/(.*\.(jpg|jpeg|png|gif|bmp))",
                    "description": "Path to the input image file."
                },
                "output_path": {
                    "type": "string",
                    "pattern": r".*/.*",
                    "description": "Path to save the processed image."
                },
                "resize": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "minItems": 2,
                    "maxItems": 2,
                    "description": "Optional. Resize dimensions as [width, height]."
                }
            },
            "required": ["image_path", "output_path"]
        }
    },
    {
        "name": "B9",
        "description": "Convert a Markdown file to another format and save the result to the specified output path.",
        "parameters": {
            "type": "object",
            "properties": {
                "md_path": {
                    "type": "string",
                    "pattern": r".*/(.*\.md)",
                    "description": "Path to the Markdown file to be converted."
                },
                "output_path": {
                    "type": "string",
                    "pattern": r".*/.*",
                    "description": "Path where the converted file will be saved."
                }
            },
            "required": ["md_path", "output_path"]
        }
    }
]

def get_completions(prompt: str):
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{openai_api_chat}",
            headers=headers,
            json=
                {
                    "model": "gpt-4o-mini",
                    "messages": [
                                    {"role": "system", "content": "You are a function classifier that extracts structured parameters from queries."},
                                    {"role": "user", "content": prompt}
                                ],
                    "tools": [
                                {
                                    "type": "function",
                                    "function": function
                                } for function in function_definitions_llm
                            ],
                    "tool_choice": "auto"
                },
        )
    # return response.json()
    print(response.json()["choices"][0]["message"]["tool_calls"][0]["function"])
    return response.json()["choices"][0]["message"]["tool_calls"][0]["function"]

# Placeholder for task execution
@app.post("/run")
async def run_task(task: str):
    try:
        # Placeholder logic for executing tasks
        # Replace with actual logic to parse task and execute steps
        # Example: Execute task and return success or error based on result
        # llm_response = function_calling(tast), function_name = A1
        response = get_completions(task)
        print(response)
        task_code = response['name']
        arguments = response['arguments']

        if "A1"== task_code:
            A1(**json.loads(arguments))
        if "A2"== task_code:
            A2(**json.loads(arguments))  
        if "A3"== task_code:
            A3(**json.loads(arguments))  
        if "A4"== task_code:
            A4(**json.loads(arguments))
        if "A5"== task_code:
            A5(**json.loads(arguments))  
        if "A6"== task_code:
            A6(**json.loads(arguments))   
        if "A7"== task_code:
            A7(**json.loads(arguments)) 
        if "A8"== task_code:
            A8(**json.loads(arguments)) 
        if "A9"== task_code:
            A9(**json.loads(arguments)) 
        if "A10"== task_code:
            A10(**json.loads(arguments)) 

        if "B3" == task_code:
            B3(**json.loads(arguments))
        if "B5" == task_code:
            B5(**json.loads(arguments))  
        if "B6" == task_code:
            B6(**json.loads(arguments)) 
        if "B7" == task_code:
            B7(**json.loads(arguments))
        if "B9" == task_code:
            B9(**json.loads(arguments))               
        return {"message": f"{task_code} Task '{task}' executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Placeholder for file reading
@app.get("/read", response_class=PlainTextResponse)
async def read_file(path: str = Query(..., description="File path to read")):
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
