from datetime import datetime, timedelta
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, constr, validator
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
import pytz 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

class TodoItem(BaseModel):
    title: str
    description: str
    created_date: datetime
    target: str

    @validator('target')
    def target_must_be_valid_datetime(cls, v):
        try:
            return datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError('Invalid target format. Please use YYYY-MM-DD HH:MM:SS.')

class TodoItemDB(Base):
    __tablename__ = "todo_items"

    id = Column(Integer, unique=True, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=func.now())
    target = Column(String)
    # time_remaining = Column(Integer)

#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def format_datetime(datetime_obj):
    return func.strftime('%Y-%m-%d %H:%M:%S', datetime_obj)


# def calculate_time_remaining(created_date_str: str, target_date_str: str) -> str:
#     # Get the Kolkata timezone
#     kolkata_timezone = pytz.timezone('Asia/Kolkata')
    
#     # Convert the created_date_str and target_date_str to datetime objects
#     # created_date = datetime.strptime(created_date_str, "%Y-%m-%d %H:%M:%S")
#     target_date = datetime.strptime(target_date_str, "%Y-%m-%d %H:%M:%S")
    
#     # Convert the created_date and target_date to Kolkata timezone
#     created_date = kolkata_timezone.localize(created_date)
#     target_date = kolkata_timezone.localize(target_date)
    
#     # Get the current time in Kolkata timezone
#     now = datetime.now(kolkata_timezone)
    
#     # Calculate remaining time
#     remaining_time = target_date - now
    
#     return str(remaining_time)

def create_todo_item(db: Session, todo_item: TodoItem):
    db_todo = TodoItemDB(title=todo_item.title, description=todo_item.description, target=todo_item.target)
    # db_todo.created_date = datetime.fromisoformat(db_todo.created_date)
    # target_datetime = datetime.strptime(todo_item.target, "%Y-%m-%d %H:%M:%S")
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    # created_str = DateTime.strptime(TodoItem.created_date, '%Y-%m-%d %H:%M:%S')
    # time_reaming=func.timedelta(target_str - created_str)
    return db_todo
    
@app.post("/todos/", response_model=list[TodoItem])
def create_todo(todo_item: TodoItem, db: Session = Depends(get_db)):
    db_todo = create_todo_item(db, todo_item)
    return [db_todo]

@app.get("/todos/", response_model=List[TodoItem])
def read_todos(item_id: int = None, skip: int = 0, limit: int = None, Query: str = None, aggregate: str = None, db: Session = Depends(get_db)):
    query = db.query(TodoItemDB)
    if item_id:
        query = query.filter(TodoItemDB.id == item_id)
    elif Query:
        query = query.filter(TodoItemDB.title.contains(Query) | TodoItemDB.description.contains(Query) | TodoItemDB.target.contains(Query))
    todos = query.offset(skip).limit(limit).all()
    # for todo in todos:
    #     todo.time_remaining = calculate_time_remaining(todo.created_date, todo.target)
    return todos

print
@app.put("/todos/{id}", response_model=TodoItem)
def update_todo(id: int, updated_todo: TodoItem, db: Session = Depends(get_db)):
    db_todo = db.query(TodoItemDB).filter(TodoItemDB.id == id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo item not found")
    db_todo.title = updated_todo.title
    db_todo.description = updated_todo.description
    db_todo.target = updated_todo.target
    db.commit()
    return TodoItem(id=db_todo.id, title=db_todo.title, description=db_todo.description, created_date=db_todo.created_date, target=db_todo.target)

@app.delete("/todos/{id}")
def delete_todo(id: int, db: Session = Depends(get_db)):
    db_todo = db.query(TodoItemDB).filter(TodoItemDB.id == id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo item not found") 
    db.delete(db_todo)
    # db.query(TodoItemDB).filter(TodoItemDB.id > id).update({TodoItemDB.id: TodoItemDB.id - 1})
    db.commit()
    return {"message": "Todo item deleted successfully"}


