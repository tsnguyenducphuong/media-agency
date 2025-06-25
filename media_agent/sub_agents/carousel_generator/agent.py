from google.adk.agents import LlmAgent
 

from media_agent.tools import create_carousel_image 

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')


carousel_generator_agent = LlmAgent(
    name="carousel_generator",
    model=LLMAGENT_MODEL,
    description="Image Carousel Generator Agent. This agent helps to generate beautiful carousel image from a single input image.",
    instruction="""
    You are a helpful assistant that generate beautiful carousel image using the following tool:
    - create_carousel_image
  
    Once the tool is finished, handover to next agent
    """,
    
    tools=[create_carousel_image],
     
)