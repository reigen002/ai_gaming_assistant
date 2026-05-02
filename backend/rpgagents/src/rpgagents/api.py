from datetime import datetime
import logging
import os

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rpgagents.conversation_store import ConversationStore
from rpgagents.main import quick_search
from rpgagents.worker import run_crew_task

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RPG_API")

app = FastAPI(
    title="RPG Gaming Assistant API",
    description="High-performance SaaS API for RPG Game Guides",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_store = ConversationStore()

class QueryRequest(BaseModel):
    game_name: str
    query: str

class TaskResponse(BaseModel):
    task_id: str
    status: str

class QueryResponse(BaseModel):
    game: str
    query: str
    result: str
    timestamp: str


class ConversationCreateRequest(BaseModel):
    game_name: str
    title: str | None = None


class ConversationResponse(BaseModel):
    id: str
    game_name: str
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


class ChatRequest(BaseModel):
    game_name: str
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    game_name: str
    answer: str
    timestamp: str

@app.get("/health")
def health_check():
    return {"status": "online", "model": "gemini-flash-latest", "version": "2.0.0"}


@app.get("/widget")
def get_widget():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    widget_path = os.path.join(base_dir, "static", "game_slidebar.html")

    if not os.path.exists(widget_path):
        raise HTTPException(status_code=404, detail="Widget not found")

    return FileResponse(widget_path)

@app.post("/ask", response_model=TaskResponse)
def ask_question(request: QueryRequest):
    """
    Submit a game guide request for asynchronous processing.
    """
    try:
        logger.info(f"Submitting task: {request.game_name} -> {request.query}")
        
        # Dispatch task to Celery
        task = run_crew_task.delay(request.game_name, request.query)
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING"
        )

    except Exception as e:
        logger.error(f"Error submitting task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations", response_model=ConversationResponse)
def create_conversation(request: ConversationCreateRequest):
    conversation_id = conversation_store.create_or_get_conversation(
        game_name=request.game_name,
        title=request.title,
    )
    convo = conversation_store.get_conversation(conversation_id)
    if convo is None:
        raise HTTPException(status_code=500, detail="Unable to create conversation")
    return convo


@app.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(game_name: str | None = None):
    return conversation_store.list_conversations(game_name=game_name)


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str):
    convo = conversation_store.get_conversation(conversation_id)
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@app.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_conversation_messages(conversation_id: str):
    convo = conversation_store.get_conversation(conversation_id)
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation_store.get_messages(conversation_id)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        conversation_id = conversation_store.create_or_get_conversation(
            game_name=request.game_name,
            conversation_id=request.conversation_id,
            title=f"{request.game_name} chat",
        )

        conversation_store.add_message(conversation_id, "user", request.message)

        answer = quick_search(request.game_name, request.message)

        conversation_store.add_message(conversation_id, "assistant", answer)

        return ChatResponse(
            conversation_id=conversation_id,
            game_name=request.game_name,
            answer=answer,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
def get_status(task_id: str):
    """
    Check the status of a background task.
    """
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.status == "PROGRESS":
        response["message"] = task_result.info.get("message", "")
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.info)
        
    return response

@app.get("/result/{task_id}", response_model=QueryResponse)
def get_result(task_id: str):
    """
    Retrieve the finished guide result.
    """
    task_result = AsyncResult(task_id)
    
    if not task_result.ready():
        raise HTTPException(status_code=400, detail="Task not finished yet")
        
    if task_result.failed():
        raise HTTPException(status_code=500, detail="Task failed")
        
    result_data = task_result.result
    
    return QueryResponse(
        game=result_data['game'],
        query=result_data['query'],
        result=result_data['result'],
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    # Allow running directly for testing
    uvicorn.run(app, host="0.0.0.0", port=8000)
