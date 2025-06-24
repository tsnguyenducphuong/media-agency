from google.adk.agents import SequentialAgent,ParallelAgent

from .sub_agents.media_collector import media_collector_agent

from .sub_agents.background_replacer import background_replacer_agent
from .sub_agents.background_whiter import background_whiter_agent
from .sub_agents.carousel_generator import carousel_generator_agent
from .sub_agents.greatings_agent import greatings_agent
from .sub_agents.image_upscaler import image_upscaler_agent
from .sub_agents.multi_angles_generator import multi_angles_generator_agent
from .sub_agents.product_video_generator import product_video_generator_agent
from .sub_agents.skia_effect import skia_effect_agent
from .sub_agents.thumbnail_generator import thumbnail_generator_agent

from .sub_agents.product_descriptor_a2a_client import product_descriptor_a2a_client_agent 
 
 
# Create Parallel Agent to create professional media (images, video) from raw products’ images concurrently ---
media_processing_parallel = ParallelAgent(
    name="media_processing_parallel",
    sub_agents=[ 
        background_replacer_agent, #ok 2
        carousel_generator_agent, #ok 2
        # image_upscaler_agent,     #ok local, not ok GCS
        multi_angles_generator_agent,#ok 2
        # product_video_generator_agent, #ok local
        # skia_effect_agent, #ok not use
        # thumbnail_generator_agent, #ok, not use
        # product_descriptor_a2a_client_agent #ok
        ],
    description="Transform the raw products’ images into studio quality images and video, ready for ecommerce"
)
 
media_agent = SequentialAgent(
    name="EcommeceMediaAgency",
    sub_agents=[
                #greatings_agent, #Step 0: greating the user and ready to start the e-commerce media content generation process
                media_collector_agent, #Step 1: Get the folder contains raw product images, and ask for brand background image. Put into context
                # background_whiter_agent, #Step 2: Standardize all images with white background 
                media_processing_parallel #Step 3: Loop through the image list and parallel processing with specific agents like: upscaler, thumbnail generator, video generator, etc.
                ],
    description="Generates studio quality images, and video through parallel image processing with several subagents",
)

root_agent = media_agent
