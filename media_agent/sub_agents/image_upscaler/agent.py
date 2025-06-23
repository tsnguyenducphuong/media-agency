from google.adk.agents import LlmAgent 

from media_agent.tools import  image_upscale

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')


image_upscaler_agent = LlmAgent(
    name="image_upscaler",
    model=LLMAGENT_MODEL,
    description="Image Upscaler Agent. This agent will upscale the images in the media folder (specified by user) by default scale factor of 2",
    instruction="""
    You are a helpful assistant that upscale image using the following tool:
    - image_upscale
    
    Once the tool is finished, handover to next agent
    """,
    
    tools=[image_upscale],
     
)