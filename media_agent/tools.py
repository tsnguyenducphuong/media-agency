from datetime import datetime
import time

import uuid
import re

from google import genai
from google.genai import types
from google.oauth2 import service_account

from google.genai.types import Image as googleImage

 
from io import BytesIO
import skia
import numpy as np

from google.cloud import storage

from dotenv import load_dotenv

from media_agent.schemas.user import UserSelection
import json


import os
from PIL import Image  
import PIL.Image
 
 
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext

import base64
import asyncio
import nest_asyncio
import httpx
import logging
from uuid import uuid4

from a2a.client import A2AClient
from a2a.types import JSONRPCErrorResponse,Part, FilePart,FileWithBytes, Message, MessageSendParams, Role, TaskStatus, TextPart,SendMessageRequest,GetTaskRequest,GetTaskResponse,SendMessageResponse,SendMessageSuccessResponse, Task,TaskQueryParams,GetTaskSuccessResponse,TaskState
from a2a.client import A2ACardResolver

 

# from a2a.types import FilePart, Message, MessageSendParams, Role, TaskStatus, TextPart


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) 

load_dotenv()
nest_asyncio.apply()

APIKEY = os.getenv("GOOGLE_API_KEY")

IMAGE_EDIT_MODEL=os.getenv("IMAGE_EDIT_MODEL","gemini-2.5-flash-preview-05-20")
# IMAGE_EDIT_MODEL=os.getenv("IMAGE_EDIT_MODEL","imagen-3.0-capability-001")

ENABLE_VERTEXAI=os.getenv("ENABLE_VERTEXAI",False)
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT","ecommerce-media-agency")
VIDEO_MODEL  = os.getenv("VIDEO_MODEL","veo-3.0-generate-preview")
LOCATION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
IS_USE_VEO3=os.getenv("IS_USE_VEO3",False) 
 
IS_USE_GCS=(os.getenv('IS_USE_GCS', 'False') == 'True')

PROCESSED_FOLDER=os.getenv("PROCESSED_FOLDER","processed_media")
WHITEBACKGROUND_FOLDER=os.getenv("WHITEBACKGROUND_FOLDER","white_background")
 
def _load_precreated_defaultvalues(callback_context: CallbackContext):
    """
    Sets up the initial state.
    Set this as a callback as before_agent_call of the root_agent.
    This gets called before the system instruction is contructed.

    Args:
        callback_context: 

    """  
    callback_context.state["media_folder"] = ""
    callback_context.state["brand_image_path"] = ""
    
    # return {"action": "_load_precreated_defaultvalues", "media_folder": "/Users/phuongnguyen/Documents/"}

def process_folder(tool_context: ToolContext) -> dict:
    """Process all images in the selected folder."""
    
    folder_path = tool_context.state["media_folder"]
    if not folder_path:
        print("Error: No folder selected!")
        return {
            "status": "failed",
            "error":"no folder selected"
            }
    
    # Update selected folder in state via assignment
    #tool_context.state["media_folder"] = folder_path

    # Create output folder for upscaled images
    output_folder = os.path.join(folder_path, "processed_images")
    
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    # Process each image in the folder
    success_count = 0
    fail_count = 0
    
     # Create new list with the images added
    image_list = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            #image_path = os.path.join(folder_path, filename)
            success_count += 1
            image_list.append(filename)
            print("found image:" + filename)
    
    # Show summary
    if success_count > 0:
        tool_context.state["image_list"] = image_list
        message = f"Initial processing complete!\nSuccessfully add: {success_count} images for being processed by media agency"
        print("Summary:" + message)
    else:
        message = f"Found no support image (png, jpeg, gif, bmp) in the selected folder"
        print("Error:" + message)

    return {
        "description":"The media folder specified by user",
        "status": "success",
        "media folder": folder_path}
    # return image_list

def images_list_from_folder(media_folder: str) -> dict:
    """Process all images in the selected folder."""
    
    print ("images_list_from_folder entering...")

    folder_path = media_folder #tool_context.state["media_folder"]
    if not folder_path:
        print("Error: No folder selected!")
        return {"error":"no folder selected"}
    
    # Update selected folder in state via assignment
    #tool_context.state["media_folder"] = folder_path

    # Create output folder for upscaled images
    # output_folder = os.path.join(folder_path, "processed_images")
    
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    # Process each image in the folder
    success_count = 0
    fail_count = 0
    
     # Create new list with the images added
    image_list = []

    if IS_USE_GCS == True:
        print("images_list_from_folder, calling get_all_images_name_in_gcs_bucket: " + media_folder)
        # image_list = get_all_images_name_in_gcs_bucket(media_folder)
        image_list =  get_all_images_name_in_gcs_bucket(SOURCE_BUCKET_NAME=media_folder,PROCESSED_FOLDER_NAME=PROCESSED_FOLDER,WHITE_BACKGROUND_FOLDER_NAME=WHITEBACKGROUND_FOLDER)
        print ("images_list_from_folder, getting image list from gcs bucket completed.")

        return image_list
    else:
         print("images_list_from_folder, getting local images from folder: " + media_folder)

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            #image_path = os.path.join(folder_path, filename)
            success_count += 1
            image_list.append(filename)
            print("found image:" + filename)
    
    # Show summary
    if success_count > 0:
        # tool_context.state["image_list"] = image_list
        message = f"Initial processing complete!\nSuccessfully add: {success_count} images for being processed by media agency"
        print("Summary:" + message)
    else:
        message = f"Found no support image (png, jpeg, gif, bmp) in the selected folder"
        print("Error:" + message)

    # return {"description":"list of images in the media folder", "image_list": image_list, "media folder": folder_path}
    return image_list


def set_media_folder(tool_context: ToolContext, newfolder:str) -> dict:

    tool_context.state["media_folder"] =  newfolder
    return {
        "description":"The media folder specified by user",
        "status": "success",
        "media_folder": newfolder
        }

def set_brand_image_path(tool_context: ToolContext, new_brand_image_path:str) -> dict:

    tool_context.state["brand_image_path"] =  new_brand_image_path
    media_folder = tool_context.state["media_folder"]
    print ("in set_brand_image_path, media_folder=" + media_folder)
    return {
        "description":"The media folder specified by user",
        "status": "success",
        "brand_image_path":new_brand_image_path,
        # "media_folder": media_folder
    }


def resize_image(tool_context: ToolContext) -> dict:
    """Resize an image while maintaining aspect ratio."""
    try:
         # Get current media folder
        image_folder = tool_context.state["media_folder"]
        image_folder = "/Users/phuongnguyen/Documents/media-images"
        max_size = 800

        image_list = tool_context.state["image_list"]

        #image_path = os.path.join(image_folder, image_list[0])
        image_path = os.path.join(image_folder, "Magic_Fill_Cover.png")

        output_folder = os.path.join(image_folder,"processed_images")

        img = Image.open(image_path)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Save resized image
        filename = os.path.basename(image_path)
        output_path = os.path.join(output_folder, f"resized_{filename}")

        img.save(output_path, quality=95)
        # save_image_local_or_gcs(img,output_path,media_folder,)

        print(f"Resized: {filename}")
        return {"action":"resize_image", "resized_image_path":output_path}
    except Exception as e:
        print(f"Error processing in resize_image: {image_path}: {e}")
        return {"error": e}

def skia_effects(tool_context: ToolContext) -> dict:
    """Make skia effects for input image while maintaining aspect ratio."""
    try:

        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"] 
       
        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
        # Create output folder if it doesn't exist
        output_folder = os.path.join(media_folder,"processed_images")
        os.makedirs(output_folder, exist_ok=True) 

        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 
        
        output_folder = os.path.join(media_folder,"processed_images")

        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True) 

        # loop through each image in the media folder and make skia effects
        for image_name in image_list:   
            image_path = os.path.join(media_folder, image_name) 

            if not image_path:
                return {"error": "no valid image path"} 

            output_image_path = image_name.replace(".", "_skiaeffect.")
            output_path = os.path.join(output_folder,output_image_path)    

            #create skia effect images
            isImageGenerated = draw_image_with_background(
                    image_path=image_path,     # Replace with your image file
                    output_path=output_path,   # Output image path
                    bg_color=(135, 206, 250)          # Light sky blue background
            ) 

            if isImageGenerated < 0:
                return {"status": "failed"}
      
        return {
            "status": "success",
            "detail": "AI Skia effects: image created successfully and stored in output folder.", 
            "media_folder": media_folder
        }
    except Exception as e:
        print(f"Error processing in skia effect: {e}")
        return {"error in skia_effects:": e}

def background_replacer(tool_context: ToolContext) -> dict:
    """Replace input image's background with selected brand (background) image while maintaining aspect ratio."""
    try:

        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"] 
        # print ("20:30, background_replacer, context_media_folder=" + context_media_folder)

        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder or media_folder == "":
            return {"error": "not a valid media folder"}  

         # Create local output folder if it doesn't exist and configured to use local instead of GCS
        if IS_USE_GCS == False:
            # output_folder = os.path.join(media_folder,"whitebackground_images")
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True) 

        # gs://media_agency/brand/background.png
        brand_image_name= "brand/background.png"
        brand_image_path = media_folder + "/" + brand_image_name

        logger.info ("naming convention, brand_image_path=" + brand_image_path)

        # validBrandImage = is_valid_brandimage(brand_image_path)

        # if not validBrandImage:
        #     return {
        #         "status": "completed",
        #         "detail": "no valid brand image found, stop processing."
        #     }

        if IS_USE_GCS == True:
                brand_image = get_image_local_or_gcs(image_path_or_blob_name=brand_image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                logger.info("Successfully download brand image from GCS:" + brand_image_name)
        else:   
                brand_image = PIL.Image.open(brand_image_path)

        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and change the background to white
        client = genai.Client(api_key=APIKEY) 

        for image_name in image_list:   
            if IS_USE_GCS == True:
                image = get_image_local_or_gcs(image_path_or_blob_name=image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                logger.info("Successfully download image from GCS:" + image_name)
            else:
                image_path = os.path.join(media_folder, image_name) 

                if not image_path:
                    return {"error": "no valid image path"}  
                
                image = PIL.Image.open(image_path)

            output_image_path = image_name.replace(".", "_brandbackground.")
            # output_path = os.path.join(output_folder,output_image_path)  
           
            edit_prompt = ('Replace the background of image 1 with brand image background in image 2. Keep the product image consistent',)

            response = client.models.generate_content(
                model=IMAGE_EDIT_MODEL,#"gemini-2.0-flash-preview-image-generation",
                contents=[edit_prompt, image, brand_image],
                config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
                )
            )

            isImageGenerated = 0

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    isImageGenerated = 1
                    output_image = Image.open(BytesIO(part.inline_data.data))
                    # output_image.save(output_path)
                    save_image_local_or_gcs(image=output_image,output_blob_name=output_image_path,SOURCE_BUCKET_NAME=media_folder,OUTPUT_FOLDER_NAME=PROCESSED_FOLDER,isSaveGCS=IS_USE_GCS,isByteIOImage=False,byteIOImage=None)


            if isImageGenerated == 0:
                return {"status": "failed"}
        
      
        return {
            "status": "success",
            "detail": "AI Background Replacer: image created successfully and stored in output folder.",
            "brand_image_path": brand_image_path,
            "media_folder": media_folder
            }
    except Exception as e:
        print(f"Error processing in background replacer: {e}")
        return {
                "status": "error",
                "detail": e
                }
 

def image_upscale(tool_context: ToolContext) -> dict:
    """Upscale image using Skia """
    try:
       
        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"] 
        # logger.info ("image_upscale, context_media_folder:" + context_media_folder)
        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
         # Create local output folder if it doesn't exist and configured to use local instead of GCS
        if IS_USE_GCS == False:
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True)  

        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and change the background to white
        # client = genai.Client(api_key=APIKEY)

        for image_name in image_list:     

            output_image_path = image_name.replace(".", "_upscaled.")
            output_path = os.path.join(media_folder,PROCESSED_FOLDER) 
            output_path = os.path.join(output_path,output_image_path) 
 
            image_path=""

            if IS_USE_GCS == True:
                image = get_image_local_or_gcs(image_path_or_blob_name=image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                print("Successfully download image from GCS:" + image_name)
            else:
                image_path = os.path.join(media_folder, image_name) 

                if not image_path:
                    return {"error": "no valid image path"}   
                
                image = PIL.Image.open(image_path).convert('RGBA')

            #upscale image using skia
            isImageUpscaled = upscale_image_with_skia(
                image_path=image_path,     # Replace with your image file
                output_path=output_path,   # Output image path 
                upscale_factor=2,  #upscale factor
                pil_image=image,
                output_image_path=output_image_path,
                media_folder=media_folder,
                output_folder=PROCESSED_FOLDER
            )  
          
            if isImageUpscaled < 0:
                return {"status": "failed"}
      
        return {
            "status": "success",
            "detail": "AI Upscaler: image upscaled successfully and stored in output folder.", 
            "media_folder": media_folder
        }
    except Exception as e:
        print(f"Error processing in image upscale: {e}")
        return {"error in image_upscale:": e}

def generate_thumbnails(tool_context: ToolContext) -> dict:
    """Generate thumbnail image using Skia """
    try:

        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"] 
        print ("image_upscale, context_media_folder:" + context_media_folder)
        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
       # Create local output folder if it doesn't exist and configured to use local instead of GCS
        if IS_USE_GCS == False:
            # output_folder = os.path.join(media_folder,"whitebackground_images")
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True) 

        if IS_USE_GCS:
            logger.info ("generate_thumbnails, calling get_all_images_name_in_gcs_bucket..." + context_media_folder)
            image_list =  get_all_images_name_in_gcs_bucket(SOURCE_BUCKET_NAME=media_folder,PROCESSED_FOLDER_NAME=PROCESSED_FOLDER,WHITE_BACKGROUND_FOLDER_NAME=WHITEBACKGROUND_FOLDER)
        else:
            image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and generate thumbnail image (width=200) 
        for image_name in image_list:   
            image_path = os.path.join(media_folder, image_name) 

            if not image_path:
                return {"error": "no valid image path"} 

            # output_image_path = image_name.replace(".", "_thumbnail.")
            output_image_name = image_name.replace(".", "_thumbnail.")
            output_path = os.path.join(output_folder,output_image_name)  

            if IS_USE_GCS == True:
                image = get_image_local_or_gcs(image_path_or_blob_name=image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                logger.info("Successfully download image from GCS:" + image_name)
            else:
                image_path = os.path.join(media_folder, image_name) 

                if not image_path:
                    return {"error": "no valid image path"} 

                
                # output_path = os.path.join(output_folder,output_image_path) 
                image = PIL.Image.open(image_path)

            #create skia effect images
            isImageGenerated = generate_thumbnail_with_skia(
                    image_path=image_path,     # Replace with your image file
                    output_path=output_path,   # Output image path 
                    output_filename=output_image_name,
                    media_folder=media_folder
                )
 

            if isImageGenerated < 0:
                return {"status": "failed"}
      
        return {
            "status": "success",
            "detail": "AI Thumbnail: thumbnail image created successfully and stored in output folder.", 
            "media_folder": media_folder
        }
    except Exception as e:
        print(f"Error processing in generate_thumbnails: {e}")
        return {"error in generate_thumbnails:": e}


def make_whitebackground_image(tool_context: ToolContext) -> dict:
    """Make white background for input image while maintaining aspect ratio."""
    try: 

        context_media_folder = tool_context.state["media_folder"] 
        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
        # Create local output folder if it doesn't exist and configured to use local instead of GCS
        if IS_USE_GCS == False:
            # output_folder = os.path.join(media_folder,"whitebackground_images")
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True) 

        logger.info ("make_whitebackground_image, calling images_list_from_folder: " + media_folder)
        
        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and change the background to white
        client = genai.Client(api_key=APIKEY)

        for image_name in image_list:   
            output_image_path = image_name.replace(".", "_whitebackground.")
            
            if IS_USE_GCS == True:
                image = get_image_local_or_gcs(image_path_or_blob_name=image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                print("Successfully download image from GCS:" + image_name)
            else:
                image_path = os.path.join(media_folder, image_name) 

                if not image_path:
                    return {"error": "no valid image path"} 

                
                # output_path = os.path.join(output_folder,output_image_path) 
                image = PIL.Image.open(image_path)
           
            edit_prompt = ('Replace the background of this image with white background. Keep the foreground image consistent',)

            response = client.models.generate_content(
                # model="gemini-2.0-flash-preview-image-generation",
                model=IMAGE_EDIT_MODEL,
                contents=[edit_prompt, image],
                config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
                )
            )

            isImageGenerated = 0

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    isImageGenerated = 1
                    output_image = Image.open(BytesIO(part.inline_data.data))

                    # output_image.save(output_path)
                    logger.info ("make_whitebackground_image, going to save_image_local_or_gcs...")
                    save_image_local_or_gcs(image=output_image,output_blob_name=output_image_path,SOURCE_BUCKET_NAME=media_folder,OUTPUT_FOLDER_NAME=WHITEBACKGROUND_FOLDER,isSaveGCS=IS_USE_GCS,isByteIOImage=False,byteIOImage=None)

            if isImageGenerated == 0:
                return {"status": "failed"}
        
      
        return {
            "status": "success",
            "detail": "AI White background image created successfully and stored in output folder.", 
            "media_folder": media_folder
        }
    except Exception as e:
        print(f"Error processing in White background image: {e}")
        return {"error in make_whitebackground_image:": e}


def create_carousel_image(tool_context: ToolContext) -> dict:
    """Make carousel images from input image while maintaining aspect ratio."""
    try:

        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"] 
        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
         # Create local output folder if it doesn't exist and configured to use local instead of GCS
        if IS_USE_GCS == False:
            # output_folder = os.path.join(media_folder,"whitebackground_images")
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True)  

        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and change the background to white
        client = genai.Client(api_key=APIKEY)

        for image_name in image_list:   
            output_image_path = image_name.replace(".", "_carousel.")
            
            if IS_USE_GCS == True:
                image = get_image_local_or_gcs(image_path_or_blob_name=image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                logger.info("Successfully download image from GCS:" + image_name)
            else:
                image_path = os.path.join(media_folder, image_name) 

                if not image_path:
                    return {"error": "no valid image path"} 

                
                # output_path = os.path.join(output_folder,output_image_path) 
                image = PIL.Image.open(image_path)
        
   
            edit_prompt = ('Make a carousel 2x2 image from this image. Each image in the carousel contain this image with background that represent a season. Top-left image has spring background, top-right image has summer background, bottom left image has autumn background, and bottom right image has winter background. Keep the front image consistent',)

            response = client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=[edit_prompt, image],
                config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
                )
            )

            isImageGenerated = 0

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    isImageGenerated = 1
                    output_image = Image.open(BytesIO(part.inline_data.data))
                    # output_image.save(output_path)
                    save_image_local_or_gcs(image=output_image,output_blob_name=output_image_path,SOURCE_BUCKET_NAME=media_folder,OUTPUT_FOLDER_NAME=PROCESSED_FOLDER,isSaveGCS=IS_USE_GCS,isByteIOImage=False,byteIOImage=None)


            if isImageGenerated == 0:
                return {"status": "failed"}
        
       
        return {
            "status": "success",
            "detail": "AI Carousel image created successfully and stored in output folder.", 
            "media_folder": media_folder
        }
    except Exception as e:
        logger.debug(f"Error processing in generate_carousel_image: {image_path}: {e}")
        return {"error in generate_carousel_image:": e}

def generate_product_video(tool_context: ToolContext) -> dict:
    """Make product video from input image."""
    try:

        if ENABLE_VERTEXAI == False:
            return {"status":"completed","detail":"ENABLE_VERTEXAI is configured to False, skip generating video."}
        
        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"] 
        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
          # Create local output folder if it doesn't exist and configured to use local instead of GCS
        if IS_USE_GCS == False:
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True)  


        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and change the background to white
        client = genai.Client(api_key=APIKEY)

        for image_name in image_list:   
            image_path = os.path.join(media_folder, image_name) 

            if not image_path:
                return {"error": "no valid image path"} 

            lastindexDot = image_name.rindex(".") 
            output_image_path = image_name[0:lastindexDot] + ".mp4"
            output_path = os.path.join(output_folder,output_image_path)  
  
            video_prompt = ("Make a beautiful ecommerce video of this product image.")
            generate_audio = False
            my_config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                # output_gcs_uri=output_gcs,
                number_of_videos=1,
                duration_seconds=8,
                person_generation="allow_adult",  
            )

            if IS_USE_VEO3 is True:
                video_prompt = ("Make a beautiful ecommerce video of this product image. Play happy beat music")
                generate_audio = True
                my_config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                # output_gcs_uri=output_gcs,
                number_of_videos=1,
                duration_seconds=8,
                person_generation="allow_adult",
                # enhance_prompt=enhance_video_prompt,
                generate_audio=generate_audio,
            ) 

            # output_gcs = "gs://"
            my_credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
            # genai.configure(credentials)
            # Adjust scopes as needed
            scoped_credentials = my_credentials.with_scopes(
                    ['https://www.googleapis.com/auth/cloud-platform'])
            client = genai.Client(vertexai=True, project=GOOGLE_CLOUD_PROJECT, location=LOCATION, credentials=scoped_credentials)
        
            local_input_image = types.Image.from_file(location=image_path)
            input_image=types.Image(
            image_bytes=local_input_image.image_bytes,
            mime_type="image/png",)

            operation = client.models.generate_videos(
            model=VIDEO_MODEL,
            prompt=video_prompt,
            image=input_image,
            config=my_config,
            )

            isVideoGenerated = 0

            while not operation.done:
                time.sleep(30) #wait 30 seconds for video generation
                operation = client.operations.get(operation)
                print(operation)

            if operation.response: 
                isVideoGenerated = 1
                video_bytes = operation.result.generated_videos[0].video.video_bytes
                with open(output_path, "wb") as binary_file:
                    binary_file.write(video_bytes)

            if isVideoGenerated == 0:
                return {"status": "failed"}
       
        return {
            "status": "success",
            "detail": "AI Product Videos created successfully and stored in output folder.",
            "media_folder": media_folder
        }
    except Exception as e:
        print(f"Error processing in generate_product_video: {image_path}: {e}")
        return {"error in generate_product_video:": e}


def generate_multi_angles_image(tool_context: ToolContext) -> dict:
    """Make multi angels images from input image while maintaining aspect ratio."""
    try:

        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"]  
        media_folder=get_media_folder_from_context(context_media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
        if IS_USE_GCS == False:
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True) 

        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and change the background to white
        client = genai.Client(api_key=APIKEY)

        for image_name in image_list:  

            output_image_path = image_name.replace(".", "_multiangles.")
            
            if IS_USE_GCS == True:
                image = get_image_local_or_gcs(image_path_or_blob_name=image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                logger.info("Successfully download image from GCS:" + image_name)
            else:
                image_path = os.path.join(media_folder, image_name) 

                if not image_path:
                    return {"error": "no valid image path"}  
                
                # output_path = os.path.join(output_folder,output_image_path) 
                image = PIL.Image.open(image_path) 
          
            edit_prompt = ('Make a beautiful carousel 2x2 of this image, each image in the carousel shows this product image in different angle. First image show this image from left side, Second image shows this image from right side, third image shows this image from back side, and fourth image shows this image from front side. Each image is a beautiful professional photo of this image, white background for ecommerce, keep the image consistent',)
 

            response = client.models.generate_content(
                model=IMAGE_EDIT_MODEL,#"gemini-2.0-flash-preview-image-generation",
                contents=[edit_prompt, image],
                config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
                )
            )

            isImageGenerated = 0

            index = 0
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    isImageGenerated = 1
                    output_image_path = image_name.replace(".", "_multiangles_" + str(index) + ".") 
                    
                    index = index + 1
                    output_image = Image.open(BytesIO(part.inline_data.data))
                    save_image_local_or_gcs(image=output_image,output_blob_name=output_image_path,SOURCE_BUCKET_NAME=media_folder,OUTPUT_FOLDER_NAME=PROCESSED_FOLDER,isSaveGCS=IS_USE_GCS,isByteIOImage=False,byteIOImage=None)

                    # output_image.save(output_path)

            if isImageGenerated == 0:
                return {"status": "failed", "description":"Error while processing generate_multi_angles_image"}
    
        return {
            "status": "success",
            "detail": "AI Multi Angles Images created successfully and stored in output folder.",
            "media_folder": media_folder,
        }
    except Exception as e:
        print(f"Error processing in generate_multi_angles_image: {e}")
        return {"error in generate_multi_angles_image:": e}

 
 
# Load an image using PIL and convert to bytes
def load_image_bytes(image_path):
    with open(image_path, 'rb') as f:
        return f.read()

# Convert image bytes to Skia image
def skia_image_from_bytes(image_bytes):
    return skia.Image.MakeFromEncoded(image_bytes)

# Main function to draw image on background
def draw_image_with_background(image_path, output_path, bg_color=(255, 255, 255)) -> int:

    try:
        # Load image
        image_bytes = load_image_bytes(image_path)
        skia_img = skia_image_from_bytes(image_bytes)

        # Get image dimensions
        img_width = skia_img.width()
        img_height = skia_img.height()

        # Create Skia surface with the same size as the image
        surface = skia.Surface(img_width, img_height)
        canvas = surface.getCanvas()

        # Fill the canvas with the background color
        paint = skia.Paint(Color=skia.ColorSetRGB(*bg_color))
        # canvas.drawPaint(paint)
        rect = skia.Rect(0, 0, img_width, img_height)  
        paint.setStyle(skia.Paint.kFill_Style) # or skia.Paint.kStroke_Style
        canvas.drawRect(rect, paint)

        # Draw the image on top of the background
        canvas.drawImage(skia_img, 0, 0)

        # Encode surface to PNG and save to file
        image = surface.makeImageSnapshot()
        data = image.encodeToData()
        with open(output_path, 'wb') as f:
            f.write(bytes(data))

        return 0
    
    except Exception as e:
        print(f"Error in draw_image_with_background: {e}")
        return -1
    

 
def get_media_folder_from_json(json_rawdata:str) -> str:
        # Parse JSON
        json_normalized = json_rawdata.replace("json","")
        print("in get_media_folder_from_json, processing this json data: " + json_normalized)
        data = json.loads(json_normalized)

        if not data:
            return {"error: not a valid json of media folder"}

        # Access the value
        media_folder:str = data['media_folder']
      
        if not media_folder:
            return {"error: not a valid media folder"}

        return media_folder

def get_brand_image_path_from_json(json_rawdata:str) -> str:
        # Parse JSON
        json_normalized = json_rawdata.replace("json","")
        print("in get_brand_image_path_from_json, processing this json data: " + json_normalized)
        data = json.loads(json_normalized)

        if not data:
            return {"error: not a valid json of brand image path"}

        # Access the value
        brand_image_path:str = data['brand_image_path']
      
        if not brand_image_path:
            return {"error: not a valid brand_image_path"}

        return brand_image_path

def is_media_folder_specified (json_context: str) -> bool: 

    json_normalized = json_context.replace("json","")

    isValidJson = is_valid_json(json_context)
    if not isValidJson:
        return False
    
    data = json.loads(json_normalized)
    status = data["status"]
    if( not status or status == "error"):
        return False
    elif status == "success":
        return True
    else:
        return False

def get_media_folder_from_context(context_mediafolder: str) -> str:
    """Return the user selected media folder from Context"""
    try:
        media_folder = ""
        json_data = context_mediafolder
        json_data_nomalized = json_data.replace("json","")
        if is_valid_json(json_data_nomalized) == True:
            media_folder = get_media_folder_from_json(json_data_nomalized)
        else:
            media_folder = context_mediafolder

        
        result_media_folder = media_folder

        if(media_folder.find ("gs://") > 0):
            result_media_folder = media_folder.replace("gs://","")
            result_media_folder = result_media_folder.replace("/","")

        return result_media_folder


    except Exception as e:
        print(f"Error in get_media_folder_from_context: {e}")
        return {"error" :"error processing get_media_folder_from_context", "detail": e}

def get_brand_image_path_from_context(context_brand_image_path: str) -> str:
    """Return the user selected brand image path from Context"""
    try:
        brand_image_path = ""
        json_data = context_brand_image_path
        json_data_nomalized = json_data.replace("json","")
        if is_valid_json(json_data_nomalized) == True:
            brand_image_path = get_media_folder_from_json(json_data_nomalized)
        else:
            brand_image_path = context_brand_image_path

        
        return brand_image_path


    except Exception as e:
        print(f"Error in get_media_folder_from_context: {e}")
        return {"error" :"error processing get_media_folder_from_context", "detail": e}
    
def is_valid_json(json_string):
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError:
        return False

def is_valid_brandimage(brandimagepath:str):
    try:
        image = PIL.Image.open(brandimagepath)
        return True
    except Exception as e:
        return False


 

def generate_thumbnail_with_skia(image_path, output_path,output_filename,media_folder) -> int:

    try:
        # Load the image
        image = skia.Image.open(image_path)
        
        thumbnail_size = 200

        # Calculate new dimensions
        if(image.width() >= image.height()):
            new_width = int(thumbnail_size)
            new_height = int(image.height() * (thumbnail_size/image.width()))
        else: # image.width() < image.height()
            new_height = int(thumbnail_size)
            new_width = int(image.width() * (thumbnail_size/image.height()))

        thumbnail_image = image.resize(width=new_width,height=new_height)
  
        # thumbnail_image.save(output_path)
        save_image_local_or_gcs(thumbnail_image,output_path,output_filename,media_folder,IS_USE_GCS,isByteIOImage=False,byteIOImage=None)

        return 0
    except Exception as e:
        print (f"error generate_thumbnail_with_skia: {e}")
        return -1
 

def upscale_image_with_skia(image_path, output_path, upscale_factor, pil_image:Image,output_image_path,media_folder,output_folder) -> int:

    try:
        # Load the image
        if not pil_image:
            image = skia.Image.open(image_path)
        else: #convert PIL image to Skia image
            # Convert PIL Image to RGBA if not already
            # pil_image_rgba = pil_image.convert('RGBA')
    
            # Get image data as bytes
            image_bytes = pil_image.tobytes()
            # Create Skia Image with specified alpha and color types
            image = skia.Image.fromarray(
                image_bytes,
                alphaType=skia.kUnpremul_AlphaType, # Or kPremul_AlphaType depending on your needs
                colorType=skia.kRGBA_8888_ColorType
            )
        
        # Calculate new dimensions
        new_width = int(image.width() * upscale_factor)
        new_height = int(image.height() * upscale_factor)

        scaled_image = image.resize(width=new_width,height=new_height)

        # Create a new surface for the upscaled image
        # surface = skia.Surface(new_width, new_height)
    
        # # Get the canvas and paint object
        # canvas = surface.getCanvas()
        # paint = skia.Paint(
        #     antiAlias=True,  # Enable anti-aliasing for smoother scaling
        #     filterQuality=skia.FilterQuality.kHigh_FilterQuality  # High-quality scaling
        # )
    
        # # Draw the scaled image
        # canvas.scale(upscale_factor, upscale_factor)
        # canvas.drawImage(image, 0, 0, paint)
        # # Create a new image from the surface
        # scaled_image = surface.makeImageSnapshot()
        
        # Save the upscaled image
        if IS_USE_GCS == False:
            scaled_image.save(output_path)
        else:
            # Create a BytesIO object
            image_bytes_io = BytesIO()

            # Save the skia image to the BytesIO object
            # You need to specify the image format (e.g., skia.kPNG, skia.kJPEG)
            scaled_image.save(image_bytes_io, skia.kPNG)

            # After saving, the BytesIO object's internal pointer is at the end of the data.
            # To read the bytes, you need to seek back to the beginning.
            image_bytes_io.seek(0)

            save_image_local_or_gcs(image_bytes_io,output_image_path,media_folder,output_folder,IS_USE_GCS,True,image_bytes_io)


        return 0
    except Exception as e:
        print (f"error skia upscale_image: {e}")
        return -1
 

async def call_product_descriptor_a2a_server(tool_context: ToolContext) -> dict:
    """Make Product Description from input image by calling A2A server."""
    try:
        final_product_description = ""

        # logger.info ("entering call_product_descriptor_a2a_server...")
        # Get current media folder 
        context_media_folder = tool_context.state["media_folder"]  
        media_folder=get_media_folder_from_context(context_media_folder)

        # logger.info ("call_product_descriptor_a2a_server...media_folder=" + media_folder)

        if not media_folder:
            return {"error": "not a valid media folder"} 
        
        # Create output folder if it doesn't exist
        if IS_USE_GCS == False:
            output_folder = os.path.join(media_folder,PROCESSED_FOLDER)
            os.makedirs(output_folder, exist_ok=True) 

        image_list = images_list_from_folder(media_folder)  

        if not image_list:
            return {"error": "no image found in media folder: " + media_folder} 

        # loop through each image in the media folder and change the background to white
        # client = genai.Client(api_key=APIKEY)

        agent_url = "http://localhost:8080"
        # agent_url = "http://localhost:10002"
        # agent_url="https://product-description-agent-863901711660.us-central1.run.app"
        # agent_url="https://product-description-agent-863901711660.us-east1.run.app/"

        logger.info ("call_product_descriptor_a2a_server..." + agent_url)

        async with httpx.AsyncClient(timeout=30) as http_client:
        # async with httpx.AsyncClient() as client:
          logger.info(f"Discovering A2A agent at {agent_url}")
          card_resolver = A2ACardResolver(http_client, agent_url)
        #   agent_card = await A2AClient.get_agent_card(http_client, agent_url)
          agent_card = await card_resolver.get_agent_card()
          logger.info(f"A2A Agent Card received: {agent_card.name}")

        #   client = await A2AClient.get_client_from_agent_card(http_client, agent_card) 
          client = A2AClient(http_client, agent_card, url=agent_url)
         
        #   logger.info ("call_product_descriptor_a2a_server, await A2AClient.get_client_from_agent_card")

          for image_name in image_list:   
            if IS_USE_GCS == True:
                image = get_image_local_or_gcs(image_path_or_blob_name=image_name,SOURCE_BUCKET_NAME=media_folder,isUsingGCS=IS_USE_GCS)
                # 2. Create a BytesIO object
                byte_stream = BytesIO()
                
                # 3. Save the image to the BytesIO object, specifying the format (e.g., 'PNG', 'JPEG')
                image.save(byte_stream, format='PNG') 

                # 4. Get the bytes from the BytesIO object
                image_bytes = byte_stream.getvalue()
                logger.info("Successfully download image from GCS:" + image_name)
            else:
                image_path = os.path.join(media_folder, image_name) 
                if not image_path:
                    return {"error": "no valid image path"} 
 
                # image = PIL.Image.open(image_path)
                with open(image_path, "rb") as image_file:
                    image_bytes = image_file.read()
            
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            a2afile=FileWithBytes(
                    bytes=image_base64, # This is the base64 string
                    name=image_name,
                    mimeType="image/png")
                   

            file_part_for_a2a_server = FilePart(
                file=FileWithBytes(
                    bytes=image_base64, # This is the base64 string
                    name=image_name,
                    mimeType="image/png"),
                kind="file"
            )

            state = tool_context.state
            task_id = str(uuid.uuid4())#state.get("task_id", str(uuid.uuid4()))
            message_id = str(uuid.uuid4())#state.get("message_id", str(uuid.uuid4()))

            message = Message(
                role=Role.user,
                # parts=[TextPart(text="Please describe this product image for ecommerce listing."), file_part_for_a2a_server],
                parts=[TextPart(text="Please describe this product image for ecommerce listing."),file_part_for_a2a_server],
                kind="message",
                contextId=str(uuid4()),
                taskId=task_id,
                messageId=message_id
            )

           
            payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Please describe this product image for ecommerce site."},{"type":"file", "file":a2afile}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": str(uuid4()),
            },
           } 

            # logger.info("Sending task to the A2A server v3...")
            # logger.info ("call_product_descriptor_a2a_server, Sending task to the A2A server...")

            message_request_working = SendMessageRequest(
            # id=message_id, params=MessageSendParams.model_validate(payload)
            id=message_id, params=MessageSendParams(message=message),
            method="message/send"
            )

            # message_request = SendMessageRequest(
            # id=message_id, params=MessageSendParams.model_validate(MessageSendParams(message=message)),
            # method="message/send"
            # )

            message_request_payload = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload),
            method="message/send"
            )

            # logger.info ("before client.send_message v3...")

            # response = await client.send_message(message_request)

            # send_response: SendMessageResponse = await client.send_message(message_request)
            send_response: SendMessageResponse = await client.send_message(message_request_working)
            
            # send_response: SendMessageResponse = await client.send_message(message_request_payload)
            

            # logger.info ("after client.send_message v3...")
            # await client.send_message(
            #     SendMessageRequest(params=MessageSendParams(message=message))
            # )

            # Extract the task_id from the MessageSendRequest
            # task_id = response.task_id
            # if not task_id:
            #     logger.error("No task_id received from send_message response. Cannot track task.")
            #     return

            if isinstance(send_response.root,JSONRPCErrorResponse):
                response_error:JSONRPCErrorResponse = send_response.root
                print ("send_response.root error detail=" + response_error.model_dump_json())

            if isinstance(
                send_response.root, Message):
                print ("send_response.root is instance of Message")
                response_message: Message = send_response.root
                json_data = response_message.model_dump_json()
                print ("json_data= " + json_data)

            if not isinstance(
                send_response.root, SendMessageSuccessResponse
            ) or not isinstance(send_response.root.result, Task):
                print("Received a non-success or non-task response. Cannot proceed.")
                return
            
            executing_task_id = send_response.root.result.id
            # executing_task_id="0663f0ef-bdea-42fd-a197-03b2aa5b586c"
            
            logger.info(f"86c Task initiated with ID: {executing_task_id}. Polling for status...")

            # task: TaskStatus = None # Initialize task variable
            # task:Task = None
            while True:
                logger.info("calling client.get_task(task_request)...86c")
                task_request = GetTaskRequest(id=task_id,params=TaskQueryParams(id=executing_task_id))
                get_task_response: GetTaskResponse = await client.get_task(task_request)
                logger.info("called client.get_task(task_request) 86c")

                if isinstance(get_task_response.root, GetTaskSuccessResponse):  
                            task = get_task_response.root.result  
                           
                else:  
                    break   

                logger.info("called client.get_task(task_id), task.status.state..." + task.status.state)
                logger.info("called client.get_task(task_id), task.status.id..." + task.id)

              
                if task.status.state in ["completed", "failed"]:
                    break
                logger.info(f"Task status: {task.status.state}. Polling again in 5 seconds...")
                
                await asyncio.sleep(5) 

            if task.status.state == TaskState.completed: #"completed":
                logger.info("processing completed task....")
                
                if task.status.message:
                    # The last message in the task should be the agent's final reply
                    logger.info("now processing message...." + task.status.message)
                    # agent_reply_artifacts = task.artifacts[-1]
                    agent_reply_parts = task.status.message.parts
                    for part in agent_reply_parts:
                        logger.info("now processing parts....")
                        if isinstance(part, TextPart):
                            logger.info("\n--- Final Refined Image Description (from ADK A2A Agent) ---")
                            logger.info(part.text)
                            final_product_description = part.text
                            print ("call_product_descriptor_a2a_server, part.text=" + part.text)
                            break
                else:
                    # logger.warning("Task completed, but no messages received from agent.")
                    str_detail = task.model_dump_json()  
                    # output_path = "/Users/phuongnguyen/Documents/media-images/a2a_taskjsondump.txt"
                 
                    # with open(output_path, "w") as f:
                    #             f.write(str_detail)

                    # logger.debug ("successfully write to text file:" + output_path) 
                    
                    json_data = json.loads(str_detail)
                    # Extract the embedded JSON string inside the 'text' field
                    text_block = json_data['artifacts'][0]['parts'][0]['text']

                    # Extract the inner JSON string (strip the code block markers)
                    inner_json_str = re.search(r'```json\n(.*)\n```', text_block, re.DOTALL).group(1)

                    # Load the embedded JSON
                    inner_data = json.loads(inner_json_str)

                        # Extract product_description
                    product_description = inner_data['product_description']
                     
                    # logger.info("long path, product_description is empty")
                    
                    logger.info("long path, product_description=" + product_description)

                    text_file_name = image_name.replace(".png",".txt")
                    decription_output_path = "/Users/phuongnguyen/Documents/media-images/" + text_file_name
                 
                    with open(decription_output_path, "w") as f:
                                f.write(product_description)

                    print ("successfully write description to text file:" + decription_output_path) 
                    # if artifacts:
                    #     last_parts:Part = artifacts[-1]
                    #     if isinstance(last_parts, TextPart):
                    #         result_text=last_parts.text
                    #         logger.info("task.artifacts[-1].part.text=" + result_text)
            else:
                logger.error(f"Task failed. Status: {task.status.state}")
                if task.artifacts:
                    # Log the last message for error details
                    for part in task.artifacts[-1].parts:
                        if isinstance(part, TextPart):
                            logger.error(f"Error details: {part.text}")

       
        # print("send_response", send_response)

            

            # response_content = send_response.root.model_dump_json(exclude_none=True)

            # logger.info("response_content:" + response_content)

            # json_content = json.loads(response_content)

            # resp = []
            # if json_content.get("result", {}).get("artifacts"):
            #     for artifact in json_content["result"]["artifacts"]:
            #         if artifact.get("parts"):
            #             resp.extend(artifact["parts"])
            # return resp


        return {
            "status": "success",
            "detail": "AI Product Description created successfully and stored in output folder.",
            "media_folder": media_folder,
            "product_description": final_product_description,
        }
    except Exception as e:
        print(f"Error in processing in call_product_descriptor_a2a_server: {e}")
        return {"error in call_product_descriptor_a2a_server": e}

 
 # --- GCS Helper Functions ---

def get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    try:
        return storage.Client(project=GOOGLE_CLOUD_PROJECT)
    except Exception as e:
        print(f"Error creating GCS client: {e}")
        return None
    

# --- Batch Processing Function ---
def get_all_images_name_in_gcs_bucket(SOURCE_BUCKET_NAME:str, PROCESSED_FOLDER_NAME:str, WHITE_BACKGROUND_FOLDER_NAME:str)-> dict:
    """
    Lists all images in the source bucket, resizes them, and saves them to a subfolder.
    """

    image_list = []

    print("starting get_all_images_name_in_gcs_bucket ...")

    gcs_client = get_gcs_client()
    if not gcs_client:
        print("Could not connect to GCS. Aborting.")
        return

    print(f"Starting getting image names in source bucket: '{SOURCE_BUCKET_NAME}'...")

    standardized_bucket_name = SOURCE_BUCKET_NAME.replace("gs://","")
    standardized_bucket_name = standardized_bucket_name.replace("/","")

    print(f"Standardized source bucket: '{standardized_bucket_name}'...")
    
    blobs = gcs_client.list_blobs(standardized_bucket_name)
    images_processed = 0
    
    BRAND_FOLDER_NAME = "brand"
    for blob in blobs:
        # Skip folders and files already in the processed folder
        
        if blob.name.endswith('/') or blob.name.startswith(f"{PROCESSED_FOLDER_NAME}/") or blob.name.startswith(f"{BRAND_FOLDER_NAME}/") or blob.name.startswith(f"{WHITE_BACKGROUND_FOLDER_NAME}/"):
            continue

        # Check for common image extensions
        if not blob.name.lower().endswith(('.png', '.jpg', '.jpeg', 'bmp', 'gif')):
            print(f"Skipping non-image file: {blob.name}")
            continue

        # Define the output path inside the 'processed_media' folder
        # output_blob_name = f"{PROCESSED_FOLDER_NAME}/{os.path.basename(blob.name)}"
        output_blob_name = f"{os.path.basename(blob.name)}"

        image_list.append(output_blob_name)
        
        print(f"Processing '{blob.name}' -> '{output_blob_name}'")
        images_processed = images_processed + 1
        
       
            
    print("-" * 30)
    print(f"Batch processing complete. Total images in source bucket: {images_processed}.")
    return image_list


def save_image_local_or_gcs(image: Image, output_blob_name:str,SOURCE_BUCKET_NAME:str, OUTPUT_FOLDER_NAME:str, isSaveGCS: bool,isByteIOImage:bool,byteIOImage):

    try:
        if isSaveGCS == True:
            logger.info("going to upload image to GCS..." + SOURCE_BUCKET_NAME + ", output_blob_name=" + output_blob_name)

            gcs_client = get_gcs_client()
            if not gcs_client:
                return "Failed to initialize GCS client."
 
            # Get the source bucket  
            standardized_bucket_name = SOURCE_BUCKET_NAME.replace("gs://","")
            standardized_bucket_name = standardized_bucket_name.replace("/","")

            source_bucket = gcs_client.bucket(standardized_bucket_name)
            logger.info("save_image_local_or_gcs, preparing upload to bucket: " + standardized_bucket_name)

            # Save the image to an in-memory buffer
            buffer = BytesIO()
            # Determine format from output file name, default to PNG
            output_format = 'PNG'
            if output_blob_name.lower().endswith('.jpg') or output_blob_name.lower().endswith('.jpeg'):
                output_format = 'JPEG'
            
            if isByteIOImage == False:
                image.save(buffer, format=output_format)
                buffer.seek(0)
            else:
                buffer = byteIOImage

            # Define the output path inside the 'processed_folder' or 'white_background' environmetn variable
            output_blob_name = f"{OUTPUT_FOLDER_NAME}/{output_blob_name}"
        

            # Upload the resized image to the specified path in the same bucket
            destination_blob = source_bucket.blob(output_blob_name)
            destination_blob.upload_from_file(buffer, content_type=f'image/{output_format.lower()}')

            return f"Successfully upload and saved as '{output_blob_name}'."

        else:
            logger.info("going to save image local..." + SOURCE_BUCKET_NAME)
            # For example: /Users/phuongnguyen/Documents/media-images/processed_media/shoe.png
            output_blob_name = f"{SOURCE_BUCKET_NAME}/{PROCESSED_FOLDER}/{output_blob_name}"
            print("going to save image local, file path=" + output_blob_name)
            image.save(output_blob_name)

    except Exception as e:
        return f"An error occurred while processing save_image_local_or_gcs: {e}"


def get_image_local_or_gcs(image_path_or_blob_name:str,SOURCE_BUCKET_NAME, isUsingGCS:bool) -> Image:

    try:
            if isUsingGCS == True:
                print ("get_image_local_or_gcs, calling get_gcs_client...: " + image_path_or_blob_name)
                gcs_client = get_gcs_client()
                if not gcs_client:
                    return "Failed to initialize GCS client."
                else:
                    logger.info("successfully get GCS client. Downloading file...")
                # Get the source bucket and blob
                source_bucket = gcs_client.bucket(SOURCE_BUCKET_NAME)
                logger.info("got source_bucket")

                source_blob = source_bucket.blob(image_path_or_blob_name)
                logger.info("got source_bucket.blob")

                # Download the image into memory
                image_bytes = source_blob.download_as_bytes()
                logger.info("got source_blob.download_as_bytes")

                # image_bytes_decoded = image_bytes.decode("utf-8")
                # logger.info("got image_bytes.decode()")

                image = PIL.Image.open(BytesIO(image_bytes))

                logger.info ("get_image_local_or_gcs, successfully download image from bucket:" + SOURCE_BUCKET_NAME + ", blob:" + image_path_or_blob_name)

                return image

            else:
                print ("get_image_local_or_gcs, calling PIL.Image.open for local image... " + image_path_or_blob_name)
                image = PIL.Image.open(image_path_or_blob_name)
                return image

    except Exception as e:
        logger.debug(f"Error in get_image_local_or_gcs: {e}")
        return f"An error occurred while processing {image_path_or_blob_name}: {e}"
