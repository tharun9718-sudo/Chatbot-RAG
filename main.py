import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import shutil
from pathlib import Path
from rag_engine import RAGEngine

load_dotenv()

app = FastAPI(title="CHATBOT-Rag-Langchain", description='Tharun')

openai_api_key= os.getenv("OPENAI_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not present")

rag_engine = RAGEngine(openai_api_key=openai_api_key)

UPLOAD_DIR = Path('./uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

class question(BaseModel):
    question:str
    k:Optional[int]=4

class URLRequest(BaseModel):
    url:str

@app.get('/')
async def root():
    return "CHATBOT-Rag-Langchain API is active now"

@app.post('/upload_document')
async def upload_document(file: UploadFile = File(...)):

    allowed = ['.pdf', '.txt', '.doc', '.docx']
    ext = Path(file.filename).suffix.lower()

    if ext not in allowed:
        raise ValueError(f'File not supported error: {ext}')
    
    file_path = UPLOAD_DIR/file.filename
    with file_path.open('wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = rag_engine.ingest_documents(str(file_path))

    if result['status'] =='FAILED':
        raise HTTPException(500, result['message'])
    
    return result

@app.post('/ingest_url')
async def ingest_url(URL: URLRequest):
    result = rag_engine.ingest_url(URL.url)
    if result['status'] =='FAILED':
        raise HTTPException(500, result['message'])
    
    return result

@app.post('/ask_question')
async def ask_question(request: question):
    result = rag_engine.query(request.question, request.k)
    if result['status'] =='FAILED':
        raise HTTPException(500, result['message'])
    
    return result




