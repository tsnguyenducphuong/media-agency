"""media_collector_agent: for selecting media folder""" 

from google.adk.agents import LlmAgent 
from media_agent.schemas.user import UserSelection

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')

from media_agent.tools import _load_precreated_defaultvalues,set_media_folder
 

media_collector_agent = LlmAgent(
    name="media_collector",
    model= LLMAGENT_MODEL,  
    description="Collect information about media folder that contains the products' images." \
    "The media folder is the GCS bucket or the local folder in which user stores all the images for the media agency to process." \
    "Once the media folder is specified by the user, this agent will handover to other agents for image and video processing, including for example: agent to change background, upscale, generate beautiful carousel images, and generate product video and many more.",
    instruction="""
    You are a assitant agent for the Ecommerce Media Agency, ask user to specify the media folder that contains the
    products' images.

    Interacting with users using the following steps:
    1. Ask the user to provide the location of the media folder: local folder or GCS.
    Explicit mention that for the demo app, user should provide 'gs://media_agency' as testing GCS bucket
    2. Use the following tool to set the value of media folder:
      - set_media_folder
    
    3. Generate a JSON object representing the user selection, including the media folder
    4. Once the media folder is set, handover to the next agent
   
     IMPORTANT: Your response MUST be a valid JSON that matching this structure:
         {
             "description":"The media folder specified by user",
             "status": success if media_folder has specified by the user, failed if there is exception,
             "media_folder": the location the user specified, 
         }

    DO NOT include any explanations or additional text outside the structure response.
     

    Once the set_media_folder tool is complete, handover to other agent

    Remember:
    - Be helpful but not pushy
    - Emphasize the media folder should be a folder that contains supported media files, including png, jpeg, gif, and bmp images
    - Emphazise that if specify the GCS bucket for media folder, the GOOGLE CLOUD PROJECT should be configured properly and the bucket read/write permission should also configured.
    """,
    tools=[set_media_folder],
    before_agent_callback=_load_precreated_defaultvalues,
    # output_key="current_user_selection",
    # output_key="media_folder",
    # output_schema=UserSelection
)


#   3. Generate a JSON object representing the user selection, including the media folder
#     4. Once the mdia folder is set, handover to the next agent
   
#     IMPORTANT: Your response MUST be a valid JSON that matching this structure:
#         {
#             "description":"The media folder specified by user",
#             "status": success if media_folder has specified by the user, failed if there is exception,
#             "media_folder": the location the user specified, 
#         }

#         DO NOT include any explanations or additional text outside the structure response.