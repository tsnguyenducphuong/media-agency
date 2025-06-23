from google.adk.agents import LlmAgent


from media_agent.tools import generate_multi_angles_image

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')


multi_angles_generator_agent = LlmAgent(
    name="multi_angles_generator_agent",
    model=LLMAGENT_MODEL,
    description="Generate multi angles images from single input image. Multi angels images makes product's images look more beautiful." \
    "This agent will help to generate multi angles images from input images in the media folder (specified by user).",
    instruction="""
    You are a helpful assistant that generate multi angle images from input image using the following tool:
    - generate_multi_angles_image
   Once the tool is finisehd, handover to the next agent
    """,
    
    tools=[generate_multi_angles_image],
     
)