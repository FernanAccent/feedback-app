import unittest
import uuid
from app import app
from database import SessionLocal, engine, Base  # Correct import of Base from database.py
from models import LLMResponseModel  # Import the LLMResponseModel from models.py
from flask import json

class TestApp(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Create all tables in the test database
        Base.metadata.create_all(bind=engine)
    
    def setUp(self):
        # Set up the test client for Flask app
        self.app = app.test_client()
        self.app.testing = True  # Enable testing mode for the app
        # Set up the test database session
        self.db = SessionLocal()

        # Insert a dummy record into the database using the model class, not Base
        self.dummy_response = LLMResponseModel(
            session_id="test-session-id",
            user_query="What is the weather?",
            response="It's sunny today.",
            is_upvoted=False,
            feedback="Good response",
            is_refreshed=False
        )
        self.db.add(self.dummy_response)
        self.db.commit()
        self.db.refresh(self.dummy_response)  # Ensure the response_id is available

        # Store the response_id for use in the tests
        self.response_id = str(self.dummy_response.response_id)

    def tearDown(self):
        # Clean up after tests
        self.db.query(LLMResponseModel).delete()
        self.db.commit()
        self.db.close()

    def test_get_responses(self):
        # Your test for GET /responses endpoint
        response = self.app.get('/responses')
        self.assertEqual(response.status_code, 200)
    
    def test_post_responses(self):
        # Your test for POST /responses endpoint
        response = self.app.post('/responses', json={
            'session_id': '12345',
            'user_query': 'What is AI?',
            'response': 'AI is artificial intelligence.',
            'is_upvoted': False,
            'feedback': 'Good',
            'is_refreshed': False
        })
        self.assertEqual(response.status_code, 201)
    
    def test_update_feedback(self):
        # Use the response_id from the inserted dummy response
        response = self.app.put(f'/responses/{self.response_id}', json={
            'is_upvoted': True,
            'feedback': 'Excellent'
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["message"], "Feedback and/or vote updated successfully!")
    
    def test_update_feedback_not_found(self):
        # Test with a non-existing response_id
        fake_response_id = str(uuid.uuid4())  # Generate a UUID that doesn't exist
        response = self.app.put(f'/responses/{fake_response_id}', json={
            'is_upvoted': True,
            'feedback': 'Excellent'
        })
        self.assertEqual(response.status_code, 404)
        response_json = json.loads(response.data)
        self.assertEqual(response_json["error"], "Response not found")
    
    @classmethod
    def tearDownClass(cls):
        # Drop all tables in the test database
        Base.metadata.drop_all(bind=engine)

if __name__ == '__main__':
    unittest.main()
