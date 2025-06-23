# media-agency
Ecommerce Media Agency

1. Clone the source code:
gh repo clone tsnguyenducphuong/media-agency

2. Change to media-agency folder

3. Run the following command:

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

4. Change the .env variables: update your Google API Key, etc.
+ Note that for processing local images, set the environment variable (in .env file) IS_USE_GCS=False

5. Run command:
adk web

6. Navigate to http://locahost:8080

7. Say hi to the agent and specify the local folder that contain product images for processing, for example: 
    please use folder: /Users/phuongnguyen/Documents/media-images


II. Deploy to Cloud Run:
python -m venv .venv
source .venv/bin/activate
pip install google-adk

gcloud auth login

gcloud config set project ecommerce-media-agency

 
Set your Google Cloud Project ID:

export GOOGLE_CLOUD_PROJECT="ecommerce-media-agency"

Set your desired Google Cloud Location:

export GOOGLE_CLOUD_LOCATION="us-central1" # Example location
 
Set a name for your Cloud Run service (optional):

export SERVICE_NAME="media-agent-service"

Set an application name (optional):
export APP_NAME="media-agency-app"

Assuming media-agency is in the current directory: 

adk deploy cloud_run \
--project=$GOOGLE_CLOUD_PROJECT \
--region=$GOOGLE_CLOUD_LOCATION \
--service_name=$SERVICE_NAME \
--app_name=$APP_NAME \
--with_ui \
.


For connect with the A2A Server and Product Description Agents, clone the code with following command:

gh repo clone tsnguyenducphuong/product_description_a2a_server

Follow the README instruction to confiture the A2A Server and Product Description Agents. Have fun!
