import os
from typing import List
from langchain_text_splitters  import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    WebBaseLoader
)
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document


class RAGEngine:
    def __init__(self, openai_api_key: str, persist_directory: str = './chromadb'):

        self.openai_api_key = openai_api_key
        self.persist_directory = persist_directory

        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

        self.vectorestore = Chroma(
            persist_directory = persist_directory,
            embedding_function = self.embeddings
        )

        self.llm = ChatOpenAI(
            temperature=0.7,
            model_name='YOUR-OWN-MODEL',
            openai_api_key=openai_api_key
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
    def load_document(self, file_path: str) -> list[Document]:

        extension = file_path.lower().split('.')[-1]

        if extension == 'pdf':
            loader = PyPDFLoader(file_path)
        elif extension == 'txt':
            loader = TextLoader(file_path, encoding='utf-8')
        elif extension in ['doc', 'docx']:
            loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"file not supported ERROR: {extension}")
        
        return loader.load()
    
    def load_url(self, url:str) -> list[Document]:

        loader = WebBaseLoader(url)
        return loader.load()
    
    def ingest_documents(self, file_path:str) -> dict:
        try:
            documents = self.load_document(file_path)

            chunks = self.text_splitter.split_documents(documents)

            self.vectorestore.add_documents(chunks)

            return {
                "status": "SUCCESS",
                "message": f"Successfully added {len(chunks)} from {file_path}"
            }
        
        except Exception as e:
            return{
                "status": "FAILED",
                "message": str(e)
            }
        
    def ingest_url(self, url:str) -> dict:
        try:
            documents = self.load_url(url)
            chunks = self.text_splitter.split_documents(documents)

            self.vectorestore.add_documents(chunks)

            return {
                "status": "SUCCESS",
                "message": f"Successfully added {len(chunks)} from {url}"
            }
        
        except Exception as e:
            return{
                "status": "FAILED",
                "message": str(e)
            }
    
    def query(self, question:str, k:int=4)-> dict:
        try:
            collection = self.vectorestore._collection

            if collection.count() == 0:
                return{
                    "status": "SUCCESS",
                    "answer": "Hi! I'm Jenny, your AI assistant. 😊 I don't have any documents loaded yet. Please upload some documents or URLs first, and then I'll be happy to answer your questions!",
                    "sources": []
                }
            
            docs = self.vectorestore.similarity_search(question, k=k)

            if not docs:
                return {
                "status": "success",
                "answer": "Hi! I'm Jenny. 😊 I couldn't find any relevant information in the uploaded documents.",
                "sources": []
            }
            
            context = "\n\n".join([doc.page_content for doc in docs])
            

            prompt_template = """You are Jenny, a helpful AI assistant.

IMPORTANT: You can ONLY answer questions using the information provided in the Context below. 
If the answer is not in the Context, you MUST say: "I don't have that information in the documents I've been given. Please ask me about the uploaded documents."

Do NOT use your general knowledge. Do NOT make up information. ONLY use what's in the Context.

Context:
{context}

Question: {question}

Answer:"""
            
            prompt = prompt_template.format(context=context, question=question)
            response = self.llm.invoke(prompt)
            answer = response.content
            
            if not answer or "I don't have that information." in answer.lower() or "no information" in answer.lower():
                answer = "Hi! I'm Jenny. 😊 I couldn't find relevant information about that in the documents I have. Could you ask something related to the documents you've uploaded?"
           
            sources=[]
            for doc in docs:
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })

            return{
                "status": "SUCCESS",
                "answer": answer,
                "sources": sources
            }
        
        except Exception as e:
            return{
                "status": "FAILED",
                "message": str(e)
            }