from google.adk.agents import LlmAgent
 

from media_agent.tools import generate_thumbnails

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')

thumbnail_generator_agent = LlmAgent(
    name="thumbnail_generator",
    model=LLMAGENT_MODEL,
    description="Generate Image Thumbnails. This agent generate thumbnail image (by default 200px) for the images in media folder (specified by user)",
    instruction="""
    You are a helpful assistant that resize image using the following tool:
    - generate_thumbnails
    
    """,
    
    tools=[generate_thumbnails],
     
)