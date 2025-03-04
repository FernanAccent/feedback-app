import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base  # Import the Base from database.py

class LLMResponseModel(Base):
    __tablename__ = "llm_response"  # Use existing table
    
    response_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String)
    user_query = Column(String)
    response = Column(String)
    is_upvoted = Column(Boolean, nullable=True)
    feedback = Column(String, nullable=True)
    is_refreshed = Column(Boolean, default=False)
    response_timestamp = Column(DateTime, server_default=func.now())

    def __init__(self, session_id, user_query, response, is_upvoted=None, feedback=None, is_refreshed=None):
        self.session_id = session_id
        self.user_query = user_query
        self.response = response
        self.is_upvoted = is_upvoted
        self.feedback = feedback
        self.is_refreshed = is_refreshed
