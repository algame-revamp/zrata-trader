# zrata-api/main.py
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Create FastAPI instance
app = FastAPI(
    title="Zrata API",
    description="Learning FastAPI with Zrata",
    version="1.0.0"
)

# Enable CORS for frontend check
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models (data validation)
class Message(BaseModel):
    text: str
    author: Optional[str] = "Anonymous"

class User(BaseModel):
    name: str
    email: str

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# In-memory storage for learning
messages_db = []
users_db = []

# Routes
@app.get("/")
def root():
    """Root endpoint - health check"""
    return {"message": "Welcome to Zrata API!", "status": "running"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return ApiResponse(
        success=True,
        message="Zrata API is healthy",
        data={"timestamp": time.time()}
    )

# GET with path parameter
@app.get("/greet/{name}")
def greet_user(name: str):
    """Greet a specific user"""
    return {"message": f"Hello {name} from Zrata!"}

# GET with query parameters
@app.get("/search")
def search(q: str, limit: int = 10):
    """Search endpoint with query params"""
    return {
        "query": q,
        "limit": limit,
        "results": [f"Result {i+1} for '{q}'" for i in range(min(limit, 3))]
    }

# POST endpoint
@app.post("/messages")
def create_message(message: Message):
    """Create a new message"""
    new_message = {
        "id": len(messages_db) + 1,
        "text": message.text,
        "author": message.author,
        "timestamp": time.time()
    }
    messages_db.append(new_message)
    
    return ApiResponse(
        success=True,
        message="Message created successfully",
        data=new_message
    )

# GET all messages
@app.get("/messages")
def get_messages():
    """Get all messages"""
    return ApiResponse(
        success=True,
        message="Messages retrieved",
        data={"messages": messages_db}
    )

# PUT endpoint
@app.put("/messages/{message_id}")
def update_message(message_id: int, message: Message):
    """Update a message"""
    for msg in messages_db:
        if msg["id"] == message_id:
            msg["text"] = message.text
            msg["author"] = message.author
            return ApiResponse(
                success=True,
                message="Message updated",
                data=msg
            )
    
    raise HTTPException(status_code=404, detail="Message not found")

# DELETE endpoint
@app.delete("/messages/{message_id}")
def delete_message(message_id: int):
    """Delete a message"""
    global messages_db
    original_length = len(messages_db)
    messages_db = [msg for msg in messages_db if msg["id"] != message_id]
    
    if len(messages_db) < original_length:
        return ApiResponse(success=True, message="Message deleted")
    else:
        raise HTTPException(status_code=404, detail="Message not found")

# POST with form data
@app.post("/users")
def create_user(user: User):
    """Create a new user"""
    new_user = {
        "id": len(users_db) + 1,
        "name": user.name,
        "email": user.email,
        "created_at": time.time()
    }
    users_db.append(new_user)
    
    return ApiResponse(
        success=True,
        message="User created successfully",
        data=new_user
    )

@app.get("/users")
def get_users():
    """Get all users"""
    return ApiResponse(
        success=True,
        message="Users retrieved",
        data={"users": users_db}
    )

# Error handling example
@app.get("/error-demo")
def error_demo(should_error: bool = False):
    """Demonstrate error handling"""
    if should_error:
        raise HTTPException(
            status_code=400,
            detail="This is a demo error!"
        )
    return {"message": "No error occurred"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)