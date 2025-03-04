from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS  # Import the CORS extension
from database import SessionLocal  # Import the session from database.py
from models import LLMResponseModel
from sqlalchemy.orm import Session

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

# Update feedback and vote status (upvote/downvote)
@app.route("/responses/<response_id>", methods=["PUT"])
def update_feedback(response_id):
    data = request.get_json()
    with next(get_db()) as db:
        response = db.query(LLMResponseModel).filter(LLMResponseModel.response_id == response_id).first()

        if response:
            if "is_upvoted" in data:
                response.is_upvoted = data["is_upvoted"]
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
                "response_timestamp": response.response_timestamp
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
