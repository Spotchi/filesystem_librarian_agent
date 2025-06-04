import streamlit as st
import openai
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from chatbot_helpers import (
    therapist_prompt,
    communication_prompt,
    hr_prompt,
    coworker_prompt,
    escalation_categories,
    crisis_responses
)
import json
from PIL import Image

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic models
class Message(BaseModel):
    role: str
    content: str
    personality: str | None = None

class ChatHistory(BaseModel):
    messages: List[Message]

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personality" not in st.session_state:
    st.session_state.personality = "prive"

# Helper functions
def detect_escalation(text: str) -> List[str]:
    """Detect if the text contains any escalation categories using OpenAI API."""
    # Prepare the prompt for escalation detection
    messages = [
        {"role": "system", "content": """You are an escalation detection system. Your task is to analyze the given text and identify if it contains any of the following escalation categories: Drugs, Self-Harm, Depression, Suicide.
        Respond with a JSON array containing only the categories that are present in the text. If no categories are present, return an empty array.
        Be thorough in your analysis but also be careful not to over-detect. Only return categories if there is a clear indication of the issue."""},
        {"role": "user", "content": text}
    ]

    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.0,  # Low temperature for more consistent results
        max_tokens=100
    )

    try:
        # Parse the response as JSON
        detected = json.loads(response.choices[0].message.content)
        # Validate that all detected categories are valid
        return [category for category in detected if category in escalation_categories]
    except (json.JSONDecodeError, TypeError):
        # If there's any error in parsing, fall back to the original keyword matching
        return [category for category in escalation_categories if category.lower() in text.lower()]

def get_prompt_for_personality(personality: str) -> str:
    """Get the appropriate prompt based on personality."""
    prompts = {
        "prive": therapist_prompt,
        "hr": hr_prompt,
        "communicatie": communication_prompt,
        "collega": coworker_prompt
    }
    return prompts.get(personality, therapist_prompt)

def get_chatbot_response(user_input: str, personality: str) -> str:
    """Get response from OpenAI API."""
    # Check for escalation
    escalations = detect_escalation(user_input)
    if escalations:
        response = "⚠️ Escalation detected:\n"
        response += "\n".join([crisis_responses[category] for category in escalations])
        return response

    # Get the appropriate prompt
    prompt = get_prompt_for_personality(personality)
    
    # Prepare messages for the API
    messages = [
        {"role": "system", "content": prompt},
        *[{"role": msg.role, "content": msg.content} for msg in st.session_state.messages],
        {"role": "user", "content": user_input}
    ]

    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content

# Streamlit UI

col1, col2 = st.columns(2)
with col1:
    st.image("faresa/assets/bevoyLogo.png")
with col2:
    st.image("faresa/assets/faresa-logo-final.svg")
st.title("Bevoy Faresa AI Chatbot")

# Personality selector
personality = st.selectbox(
    "Choose your chatbot personality:",
    ["prive", "hr", "communicatie", "collega"],
    index=0
)

def get_avatar(personality: str) -> Image.Image | None:
    # Load image from faresa/assets
    image_path_dict = {
        "prive": "faresa/assets/prive.png",
        "hr": "faresa/assets/hr.png",
        "communicatie": "faresa/assets/communicatie.png",
        "collega": "faresa/assets/collega.png"
    }
    image_path = image_path_dict.get(personality)
    if image_path:
        return Image.open(image_path)
    return None

current_avatar = get_avatar(personality)
# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message.role, avatar=get_avatar(message.personality)):
        st.write(message.content)

# Chat input
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to chat history
    st.session_state.messages.append(Message(role="user", content=prompt))
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get and display assistant response
    with st.chat_message("assistant", avatar=current_avatar):
        response = get_chatbot_response(prompt, personality)
        st.write(response)
        st.session_state.messages.append(Message(role="assistant", content=response, personality=personality))

# Add a clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun() 