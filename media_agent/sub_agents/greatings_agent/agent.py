from google.adk.agents import  Agent

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')


greatings_agent = Agent(
    name="greatings_agent",
    # https://ai.google.dev/gemini-api/docs/models
    model=LLMAGENT_MODEL,
    description="Greeting agent",
    instruction="""
    You are a helpful assistant that greets the user. 
    Ask for the user's name and greet them by name.
    Then your task is complete, handover to the next agent.
    """,
)