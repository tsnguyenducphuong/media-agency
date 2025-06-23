from google.adk.agents import LlmAgent
 
from media_agent.tools import background_replacer

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')

background_replacer_agent = LlmAgent(
    name="background_replacer_agent",
    model=LLMAGENT_MODEL,
    description="Image Background Replacer Agent. This agent will use the selected brand image to replace the background image of all images in the media folder specified by the user." \
    "This agent will help to apply the same brand background image to all the processing images.",
    instruction="""
    You are a helpful assistant that change the image's background with default brand image (under brand subfolder of media_folder) using only the following tool:
    - background_replacer
     
    Once the tool is completed, handover to next agent
    """,
    
    tools=[background_replacer],
     
)