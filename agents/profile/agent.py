import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.profile.prompts import SYSTEM_PROMPT
from agents.profile.schemas import ProfileAgentOutput, UserProfile

# Load environment variables
load_dotenv()

# Get API key
groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

parser = PydanticOutputParser(pydantic_object=ProfileAgentOutput)


def run_profile_agent(user_input: str, history=None, current_profile=None):
    """
    history: list of {"role": "user"/"assistant", "content": "..."}
    """

    if current_profile is None:
        current_profile = UserProfile()

    if history is None:
        history = []

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    messages.append(
        HumanMessage(
            content=f"Current collected profile (update it, do not remove existing values):\n{current_profile.model_dump()}"
        )
    )

    # Add conversation history
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    # Add current user input
    messages.append(HumanMessage(content=user_input))

    # Add format instructions
    format_instructions = parser.get_format_instructions()
    messages.append(
        HumanMessage(
            content=f"Return the response in this format:\n{format_instructions}"
        )
    )

    # Call model
    response = llm.invoke(messages)

    # Parse structured output
    parsed = parser.parse(response.content)

    return parsed, response.content
