from fastapi import HTTPException
import subprocess
import sqlite3
import requests
import os
import re
import json
from pathlib import Path
from datetime import datetime
import base64
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
import markdown
from scipy.spatial.distance import cosine
import git
from dotenv import load_dotenv

load_dotenv()

AIPROXY_TOKEN = os.getenv('AIPROXY_TOKEN')


def A1(email="23f1000422@ds.study.iitm.ac.in"):
    try:
        process = subprocess.Popen(
            ["uv", "run", "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py", email],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error: {stderr}")
        return stdout
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error: {e.stderr}")
# A1()
def A2(prettier_version="prettier@3.4.2", filename="/data/format.md"):
    command = [r"C:\Program Files\nodejs\npx.cmd", prettier_version, "--write", filename]
    try:
        subprocess.run(command, check=True)
        print("Prettier executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def A3(filename='/data/dates.txt', targetfile='/data/dates-wednesdays.txt', weekday=2):
    input_file = filename
    output_file = targetfile
    weekday = weekday
    weekday_count = 0

    with open(input_file, 'r') as file:
        weekday_count = sum(1 for date in file if parse(date).weekday() == int(weekday)-1)


    with open(output_file, 'w') as file:
        file.write(str(weekday_count))

def A4(filename="/data/contacts.json", targetfile="/data/contacts-sorted.json"):
    # Load the contacts from the JSON file
    with open(filename, 'r') as file:
        contacts = json.load(file)
    
    # Sort the contacts by last_name and then by first_name
    sorted_contacts = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))
    
    # Write the sorted contacts to the new JSON file
    with open(targetfile, 'w') as file:
        json.dump(sorted_contacts, file, indent=4)

def A5(log_dir_path='/data/logs', output_file_path='/data/logs-recent.txt', num_files=10):
    log_dir = Path(log_dir_path)
    output_file = Path(output_file_path)

    # Get list of .log files sorted by modification time (most recent first)
    log_files = sorted(log_dir.glob('*.log'), key=os.path.getmtime, reverse=True)[:num_files]

    # Read first line of each file and write to the output file
    with output_file.open('w') as f_out:
        for log_file in log_files:
            with log_file.open('r') as f_in:
                first_line = f_in.readline().strip()
                f_out.write(f"{first_line}\n")

def A6(doc_dir_path='/data/docs', output_file_path='/data/docs/index.json'):
    docs_dir = doc_dir_path
    output_file = output_file_path
    index_data = {}

    # Walk through all files in the docs directory
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                # print(file)
                file_path = os.path.join(root, file)
                # Read the file and find the first occurrence of an H1
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('# '):
                            # Extract the title text after '# '
                            title = line[2:].strip()
                            # Get the relative path without the prefix
                            relative_path = os.path.relpath(file_path, docs_dir).replace('\\', '/')
                            index_data[relative_path] = title
                            break  # Stop after the first H1
    # Write the index data to index.json
    # print(index_data)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=4)    

def A7(filename='/data/email.txt', output_file='/data/email-sender.txt'):
    # Read the content of the email
    with open(filename, 'r') as file:
        email_content = file.readlines()

    sender_email = "sujay@gmail.com"
    for line in email_content:
        if "From" == line[:4]:
            sender_email = (line.strip().split(" ")[-1]).replace("<", "").replace(">", "")
            break
    
    # Get the extracted email address

    # Write the email address to the output file
    with open(output_file, 'w') as file:
        file.write(sender_email)

import base64
def png_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_string

#A8
def A8(filename='/data/credit-card.txt', image_path='/data/credit_card.png'):
    try:
        # Construct the request body for the AIProxy call
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the 16-digit credit card number from the image. Ensure the number is accurate and complete.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{png_to_base64(image_path)}"
                            }
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AIPROXY_TOKEN}"
        }

        # Make the request to the AIProxy service
        response = requests.post(
            "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers=headers,
            json=body
        )
        response.raise_for_status()

        # Extract the credit card number from the response
        result = response.json()
        card_number = result['choices'][0]['message']['content'].strip()

        # Validate the card number (16 digits)
        if not re.match(r"^\d{16}$", card_number):
            raise ValueError("Invalid card number format")

        # Write the extracted card number to the output file
        with open(filename, 'w') as file:
            file.write(card_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

#A9
def A9(filename='/data/comments.txt', output_filename='/data/comments-similar.txt'):
    try:
        # Read comments
        with open(filename, 'r') as f:
            comments = [line.strip() for line in f.readlines()]

        # Get embeddings for all comments
        headers = {
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "text-embedding-3-small",
            "input": comments
        }
        response = requests.post(
            "https://aiproxy.sanand.workers.dev/openai/v1/embeddings",
            headers=headers,
            json=data
        )
        response.raise_for_status()

        embeddings = [emb["embedding"] for emb in response.json()["data"]]
        embeddings = np.array(embeddings)

        # Find the most similar pair
        similarity = np.dot(embeddings, embeddings.T)
        np.fill_diagonal(similarity, -np.inf)  # Ignore self-similarity
        i, j = np.unravel_index(similarity.argmax(), similarity.shape)

        # Write the most similar pair to file
        with open(output_filename, 'w') as f:
            f.write(comments[i] + '\n')
            f.write(comments[j] + '\n')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
#A10
def A10(filename='/data/ticket-sales.db', output_filename='/data/ticket-sales-gold.txt', query="SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'"):
    # Connect to the SQLite database
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    # Calculate the total sales for the "Gold" ticket type
    cursor.execute(query)
    total_sales = cursor.fetchone()[0]

    # If there are no sales, set total_sales to 0
    total_sales = total_sales if total_sales else 0

    # Write the total sales to the file
    with open(output_filename, 'w') as file:
        file.write(str(total_sales))

    # Close the database connection
    conn.close()


# --- Phase B Tasks (New) ---
# Security validation
def validate_path(path: str):
    if not path.startswith('/data/'):
        raise HTTPException(400, "Path must start with /data/")

# B3: Fetch data from API
def B3(url: str, save_path: str):
    validate_path(save_path)
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'w') as f:
            f.write(response.text)
    except Exception as e:
        raise HTTPException(500, f"API fetch failed: {str(e)}")

# B4: Git operations
def B4(repo_url: str, clone_path: str, commit_message: str = "Auto-commit"):
    validate_path(clone_path)
    try:
        repo = git.Repo.clone_from(repo_url, clone_path)
        repo.git.add('--all')
        repo.index.commit(commit_message)
    except Exception as e:
        raise HTTPException(500, f"Git operation failed: {str(e)}")

# B5: SQL queries
def B5(db_path: str, query: str, output_file: str):
    validate_path(db_path)
    validate_path(output_file)
    try:
        conn = sqlite3.connect(db_path)
        result = pd.read_sql_query(query, conn)
        result.to_csv(output_file, index=False)
    except Exception as e:
        raise HTTPException(500, f"SQL query failed: {str(e)}")

# B6: Web scraping
def B6(url: str, output_file: str, selector: str):
    validate_path(output_file)
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = [element.get_text() for element in soup.select(selector)]
        with open(output_file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        raise HTTPException(500, f"Scraping failed: {str(e)}")

# B7: Image processing
def B7(image_path: str, output_path: str, width: int = None, height: int = None):
    validate_path(image_path)
    validate_path(output_path)
    try:
        img = Image.open(image_path)
        if width and height:
            img = img.resize((width, height))
        img.save(output_path)
    except Exception as e:
        raise HTTPException(500, f"Image processing failed: {str(e)}")

# B8: Audio transcription
def B8(audio_path: str, output_file: str):
    validate_path(audio_path)
    validate_path(output_file)
    # Note: Actual implementation requires Whisper/other ASR system
    raise HTTPException(501, "Audio transcription not implemented")

# B9: Markdown conversion
def B9(md_path: str, output_path: str):
    validate_path(md_path)
    validate_path(output_path)
    try:
        with open(md_path, 'r') as f:
            html = markdown.markdown(f.read())
        with open(output_path, 'w') as f:
            f.write(html)
    except Exception as e:
        raise HTTPException(500, f"Conversion failed: {str(e)}")

# B10: CSV filtering
def B10(csv_path: str, output_file: str, filters: dict):
    validate_path(csv_path)
    validate_path(output_file)
    try:
        df = pd.read_csv(csv_path)
        for col, value in filters.items():
            df = df[df[col] == value]
        df.to_json(output_file, orient='records')
    except Exception as e:
        raise HTTPException(500, f"Filtering failed: {str(e)}")
