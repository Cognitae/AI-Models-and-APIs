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

def load_model_file(model_file_path):
    """Load model parameters and system prompt from a model file."""
    params = {}
    system_prompt = ""
    current_section = None
    
    with open(model_file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('FROM'):
                params['model'] = line.split()[1].lower()  # Assumes the model name follows 'FROM'
            elif line.startswith('PARAMETER'):
                param_name, param_value = line.split()[1], line.split()[2]
                params[param_name.lower()] = float(param_value) if '.' in param_value else int(param_value)
            elif line.startswith('SYSTEM'):
                current_section = 'system'
            elif current_section == 'system' and line != '"""':
                system_prompt += line + "\n"
    
    return params, system_prompt

model_file_path = "C:\\Users\\ablack\\Documents\\GitHub\\AI Training\\Custom Modelfile\\Modelfile.txt"

# Load the model parameters and system prompt
model_params, system_prompt = load_model_file(model_file_path)

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

# Modify generate_response to include session management and model parameters
def generate_response(prompt, session_id):
    global conversation_history
    conversation_history = load_session(session_id)  # Load the session
    conversation_history.append(prompt)
    
    full_prompt = system_prompt + "\n" + "\n".join(conversation_history)
    
    data = model_params.copy()  # Start with model params loaded from the file
    data.update({
        "prompt": full_prompt,  # Use the combined prompt
    })
    
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
