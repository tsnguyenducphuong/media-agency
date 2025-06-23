from google.adk.agents import LlmAgent
 

from media_agent.tools import make_whitebackground_image 

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')

background_whiter_agent = LlmAgent(
    name="background_whiter_agent",
    model=LLMAGENT_MODEL,
    description="Make white background for image. This agent will make the background become white for all the images in the media folder (specified by user)." \
    "The white background image is a common requirement of many ecommerce platform.",
    instruction="""
    You are a helpful assistant that make the white background image using the following tool:
    - make_whitebackground_image 

    Once the tool is completed, handover to other agent

    """,
    
    tools=[make_whitebackground_image],
     
)
 
  
#     process all the images in {media_folder} with the tool make_whitebackground_image.
#     Mention explicitly the {media_folder} that will be proceed by Background wWiter Agent 
#  IMPORTANT: Your response MUST be a valid JSON that matchs this structure:
#         {
#             "status": success if the tool make_whitebackground_image succeeed, failed otherwise,
#             "media_folder": the location the user specified, 
#         }

#     DO NOT include any explanations or additional text outside the structure response.