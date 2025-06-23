from google.adk.agents import LlmAgent 

from media_agent.tools import skia_effects

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')


skia_effect_agent = LlmAgent(
    name="skia_effect_agent",
    model=LLMAGENT_MODEL,
    description="Generate Skia Effects for image. This agent generates image with special background color using skia." \
    "The input images are in media folder (specified by user)",
    instruction="""
    You are a helpful assistant that make special effects with Skia using the following tool:
    - skia_effects
    Once the tool is finisehd, handover to the next agent
    """,
    
    tools=[skia_effects],
     
)