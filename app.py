import uuid
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS  # Import the CORS extension
from database import SessionLocal  # Import the session from database.py
from models import LLMResponseModel
from sqlalchemy.orm import Session
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Enable CORS with specific origin (allow only requests from localhost:4200)
CORS(app, origins="http://localhost:4200")


# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow any frontend to connect

# Dependency to get the database session
def get_db():
    db: Session = SessionLocal()  # Creates a session object from SQLAlchemy
    try:
        yield db
    finally:
        db.close()

@app.route("/responses", methods=["GET"])
def get_responses():
    with next(get_db()) as db:  # Use the database session context manager
        responses = db.query(LLMResponseModel).all()
    return jsonify([{
        "response_id": str(resp.response_id),
        "session_id": resp.session_id,
        "user_query": resp.user_query,
        "response": resp.response,
        "is_upvoted": resp.is_upvoted,
        "feedback": resp.feedback,
        "is_refreshed": resp.is_refreshed,
        "response_timestamp": resp.response_timestamp
    } for resp in responses])

@app.route("/responses", methods=["POST"])
def add_response():
    data = request.get_json()
    with next(get_db()) as db:  # Use the database session context manager
        new_response = LLMResponseModel(
            session_id=data["session_id"],
            user_query=data["user_query"],
            response=data["response"],
            is_upvoted=data.get("is_upvoted"),
            feedback=data.get("feedback"),
            is_refreshed=data.get("is_refreshed")
        )
        db.add(new_response)
        db.commit()

        # Refresh the instance to ensure it's bound to the session and the ID is available
        db.refresh(new_response)  # Refresh the object to get the response_id


    # Emit event to all connected clients
    socketio.emit("new_response", {
        "response_id": str(new_response.response_id),
        "session_id": new_response.session_id,
        "user_query": new_response.user_query,
        "response": new_response.response,
        "is_upvoted": new_response.is_upvoted,
        "feedback": new_response.feedback,
        "is_refreshed": new_response.is_refreshed,
        "response_timestamp": new_response.response_timestamp
    })

    return jsonify({"message": "Response added successfully!"}), 201

@app.route("/responses/<response_id>", methods=["PUT"])
def update_feedback(response_id):
    data = request.get_json()

    # Convert response_id to UUID
    try:
        response_uuid = uuid.UUID(response_id)
    except ValueError:
        return jsonify({"error": "Invalid UUID format"}), 400

    with next(get_db()) as db:
        response = db.query(LLMResponseModel).filter(LLMResponseModel.response_id == response_uuid).first()

        if response:
            # Handle is_upvoted logic (Upvote / Downvote)
            if "is_upvoted" in data:
                if data["is_upvoted"] is True:
                    # If is_upvoted is True, set it to None if it's already True
                    if response.is_upvoted is True:
                        response.is_upvoted = None  # Un-vote if already upvoted
                    else:
                        response.is_upvoted = True  # Set to True (upvote)
                elif data["is_upvoted"] is False:
                    # If is_upvoted is False, set it to False (downvote)
                    if response.is_upvoted is False:
                        response.is_upvoted = None  # Un-vote if already downvoted
                    else:
                        response.is_upvoted = False  # Set to False (downvote)
                else:
                    # If is_upvoted is None or no value, set to None (remove vote)
                    response.is_upvoted = None

            # Handle feedback logic
            if "feedback" in data:
                response.feedback = data["feedback"]

            db.commit()

            # Emit the updated data to all connected clients
            socketio.emit("feedback_updated", {
                "response_id": str(response.response_id),
                "session_id": response.session_id,
                "user_query": response.user_query,
                "response": response.response,
                "is_upvoted": response.is_upvoted,
                "feedback": response.feedback,
                "is_refreshed": response.is_refreshed,
                "response_timestamp": response.response_timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
            })

            return jsonify({"message": "Feedback and/or vote updated successfully!"}), 200
        else:
            return jsonify({"error": "Response not found"}), 404


# Socket.IO event listener (for debugging)
@socketio.on("connect")
def handle_connect():
    print("Client connected!")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected!")

if __name__ == "__main__":
    socketio.run(app, debug=True)
