from google.adk.agents import LlmAgent
 

from media_agent.tools import call_product_descriptor_a2a_server 

import os
from dotenv import load_dotenv

load_dotenv()

LLMAGENT_MODEL = os.getenv('LLMAGENT_MODEL')

product_descriptor_a2a_client_agent = LlmAgent(
    name="product_descriptor_a2a_client",
    model=LLMAGENT_MODEL,
    description="Make product description from product image. This agent will make the product description using the tool call_product_descriptor_a2a_server." \
    "The product description will be used for ecommerce platform.",
    instruction="""
    You are a helpful assistant that make the product description from product image using the following tool:
    - call_product_descriptor_a2a_server 

    Once the tool is completed, handover to other agent

    """,
    
    tools=[call_product_descriptor_a2a_server],
     
)
 