from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging
import json
import os
import re

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Blueprint
chat_bp = Blueprint('chat', __name__)

# Simple in-memory storage for chat messages
# In a production environment, this would be a database
chat_storage = {}

# Simple keyword-based response system
auto_responses = {
    'interest rate': 'Interest rates vary based on market conditions, your credit score, and loan type. Our calculator uses current market rates by default, but you can adjust them in the form.',
    'down payment': 'Down payment is typically 3-20% of the home price. Conventional loans often require at least 5%, while FHA loans can be as low as 3.5%.',
    'closing costs': 'Closing costs generally range from 2-5% of the loan amount and include fees for loan origination, appraisal, title search, and more.',
    'pmi': 'Private Mortgage Insurance (PMI) is typically required when your down payment is less than 20% on a conventional loan. It protects the lender if you default.',
    'mip': 'Mortgage Insurance Premium (MIP) is required for FHA loans regardless of down payment amount. It includes both an upfront premium and annual premiums.',
    'va loan': 'VA loans are available to service members, veterans, and eligible surviving spouses. They often require no down payment and no private mortgage insurance.',
    'fha loan': 'FHA loans have more lenient credit requirements and allow for lower down payments (as low as 3.5%), but require mortgage insurance for the life of the loan in most cases.',
    'usda loan': 'USDA loans are for rural and suburban homebuyers who meet income eligibility. They offer 100% financing with no down payment required.',
    'conventional loan': 'Conventional loans typically require higher credit scores and down payments than government-backed loans, but may have lower overall costs.',
    'loan term': 'Common mortgage terms are 15, 20, and 30 years. Shorter terms have higher monthly payments but lower total interest costs.',
    'hello': 'Hello! How can I help you with your mortgage calculation today?',
    'hi': 'Hi there! Do you have questions about the mortgage calculator?',
    'help': 'I can help answer questions about mortgage types, rates, down payments, and how to use this calculator. What would you like to know?'
}

def get_chat_file_path(session_id):
    """Get the file path for a chat session's storage file"""
    chat_dir = os.path.join(os.path.dirname(__file__), 'chats')
    
    # Create directory if it doesn't exist
    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)
    
    # Sanitize session ID to prevent directory traversal
    safe_session_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
    
    return os.path.join(chat_dir, f'chat_{safe_session_id}.json')

def load_chat_session(session_id):
    """Load chat messages for a session from file storage"""
    file_path = get_chat_file_path(session_id)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error loading chat session {session_id}")
            return {"messages": []}
    return {"messages": []}

def save_chat_session(session_id, data):
    """Save chat messages for a session to file storage"""
    file_path = get_chat_file_path(session_id)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Error saving chat session {session_id}: {str(e)}")
        return False

def get_auto_response(message):
    """Generate automatic response based on keywords in message"""
    message_lower = message.lower()
    
    for keyword, response in auto_responses.items():
        if keyword in message_lower:
            return response
    
    # Default response if no keywords match
    return None

@chat_bp.route('/api/chat/message', methods=['POST'])
def handle_message():
    """Handle incoming chat messages"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ['session_id', 'user', 'message']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    session_id = data['session_id']
    user = data['user']
    message = data['message']
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    # Load existing chat session
    chat_data = load_chat_session(session_id)
    
    # Add the new message
    chat_data["messages"].append({
        "user": user,
        "text": message,
        "timestamp": timestamp
    })
    
    # Get automatic response if available
    auto_response = get_auto_response(message)
    
    # If we have an auto response, add it to the chat history
    if auto_response:
        chat_data["messages"].append({
            "user": "Support",
            "text": auto_response,
            "timestamp": datetime.now().isoformat()
        })
    
    # Save updated chat
    save_chat_session(session_id, chat_data)
    
    # Return response
    return jsonify({
        "success": True,
        "response": auto_response
    })

@chat_bp.route('/api/chat/history', methods=['GET'])
def get_history():
    """Get chat message history for a session"""
    session_id = request.args.get('session')
    
    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400
    
    # Load chat session
    chat_data = load_chat_session(session_id)
    
    return jsonify(chat_data)

@chat_bp.route('/api/chat/updates', methods=['GET'])
def get_updates():
    """Get new messages since last check"""
    session_id = request.args.get('session')
    last_timestamp = request.args.get('last', '')
    
    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400
    
    # Load chat session
    chat_data = load_chat_session(session_id)
    
    # If no last timestamp, return all messages
    if not last_timestamp:
        return jsonify(chat_data)
    
    # Filter messages newer than last_timestamp
    new_messages = [
        msg for msg in chat_data.get("messages", [])
        if msg.get("timestamp", "") > last_timestamp
    ]
    
    return jsonify({"messages": new_messages})
