from google.adk.agents import LlmAgent 

from media_agent.tools import generate_product_video

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')

product_video_generator_agent = LlmAgent(
    name="product_video_generator_agent",
    model=LLMAGENT_MODEL,
    description="Make beautiful product video from product image. This agent creates beautiful product video for the images in media folder (specified by user).",
    instruction="""
    You are a helpful assistant that generate product video from input image using the following tool:
    - generate_product_video 
    """,
    
    tools=[generate_product_video],
     
)