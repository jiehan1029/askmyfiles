# backend/app.py
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os


app = FastAPI()

origins = [
    "http://localhost:80",
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods
    allow_headers=["*"], # Allows all headers
)

@app.get("/health")
def health_check(request: Request):
    return {"health": "ok"}


# Define a model for the search request
class SearchRequest(BaseModel):
    query: str
    directory: str


# Endpoint to accept search requests
@app.post("/search/")
async def search_documents(request: SearchRequest):
    directory = request.directory
    query = request.query
    
    # Get all texts from the directory
    documents = process_directory(directory)

    # Implement search logic here (semantic search, full-text search, etc.)
    # For now, just return the document texts
    return {"documents": documents}


def process_directory(directory_path):
    texts = []
    # Walk through the directory to process all files
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.pdf'):
                print(f"PDF detected: {file}")
                file_path = os.path.join(root, file)
                text = extract_text_from_pdf(file_path)
                texts.append(text)
            elif file.endswith('.docx'):
                print(f"Docx detected: {file}")
                file_path = os.path.join(root, file)
                text = extract_text_from_docx(file_path)
                texts.append(text)
    return texts


# File parser functions (example)
def extract_text_from_pdf(file_path):
    import pdfplumber
    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


def extract_text_from_docx(file_path):
    from docx import Document
    doc = Document(file_path)
    text = ''
    for para in doc.paragraphs:
        text += para.text
    return text
