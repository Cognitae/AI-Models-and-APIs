import requests
import json
import gradio as gr
from datetime import datetime
import os

# Endpoint URL
url = 'http://localhost:11434/api/generate'

# Headers to indicate JSON content
headers = {'Content-Type': 'application/json'}

# Initialize or load conversation history
conversation_history = []

# Session management functions
def save_session(session_id, history):
    """Save the conversation history to a file."""
    with open(f'session_{session_id}.json', 'w') as f:
        json.dump(history, f)

def load_session(session_id):
    """Load the conversation history from a file."""
    try:
        with open(f'session_{session_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # Return an empty list if the session file does not exist

# Modify generate_response to include session management
def generate_response(prompt, session_id):
    global conversation_history
    conversation_history = load_session(session_id)  # Load the session
    conversation_history.append(prompt)
    
    full_prompt = "\n".join(conversation_history)
    data = {"model": "llama2", "prompt": full_prompt}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        full_response = ""
        try:
            for line in response.text.strip().split('\n'):
                part = json.loads(line)
                full_response += part.get('response', '')
                if part.get('done', False):
                    break
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
            return "Failed to process the API response."
        
        conversation_history.append(full_response)
        save_session(session_id, conversation_history)  # Save the updated session
        return full_response if full_response else "No response found."
    else:
        return f"Error: {response.status_code} {response.text}"

# Interface with improved instructions
iface = gr.Interface(
    fn=lambda prompt, session_id='default': generate_response(prompt, session_id),
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter your prompt here..."), 
        gr.Textbox(value="default", placeholder="Enter a session ID or use 'default'")
    ],
    outputs="text",
    title="Conversational AI with Session Management",
    description="""Enter your prompt in the text box above. Use the Session ID field to start a new session or recall an existing one. 
                   If you're continuing a session, enter the ID you used previously. Leave it as 'default' or enter a new ID to start a new session. 
                   This allows you to pause and resume conversations with the AI."""
)

iface.launch()
