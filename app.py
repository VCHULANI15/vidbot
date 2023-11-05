###########################
# Importing the libraries #
###########################
import openai
import os
import re
from dotenv import load_dotenv
from pytube import YouTube
from googleapiclient.discovery import build
import sqlite3
import datetime
import time
import threading
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

#######################################
# Creating Flask Application instance #
#######################################
app = Flask(__name__)
CORS(app)

####################################
# Loading the OpenAI API Libraries #
####################################
# Load Environment Variable
load_dotenv()
print('Environment loaded successfully!')

# Setting up the API key
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

##########################################
# Building the YouTube Connection object #
##########################################
#Importing relevant libraries
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Specify the scope(s) as a list when creating the credentials
# Set the path to your service account key file
SERVICE_ACCOUNT_FILE = 'gen-ai-hackathon-2023-4f4115699eba.json'

# Define the API version and scope
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/youtube.force-ssl']

# Create credentials from the service account key file
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Create the YouTube service
youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

# Checkpoint
print('YouTube service successfully built!')


########################################################
# Defining elements for the Flask application instance #
########################################################

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.get_json()['user_message']
    bot_response = generate_summary(user_message)
    return jsonify({"response": bot_response})

@app.route('/summarize', methods=['POST'])
def generate_summary(prompt):
    # Extract video URL from the prompt
    video_url = prompt

    # Get video transcript
    captions = get_captions(video_id)

    # Create a prompt to summarize the video
    prompt = f'Summarize the key points of the YouTube video using its captions. Here are the video captions \n {captions}'

    # Send the prompt to be summarized by OpenAI
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": "You are a summarization helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the summary from the OpenAI response
    summary = response['choices'][0]['message']['content']

    return summary
####################################################################
# Defining a function to retrive the YouTube video ID from the url #
####################################################################
@app.route('/video_id', methods=['POST'])
def get_video_id(url):
    # Regular expression pattern to match YouTube video IDs in URLs
    pattern = r'(?:youtu\.be/|youtube\.com/watch\?v=|/videos/|embed/|watch\?v=|user/|v=|embed/?\S+/|'
    pattern += r'\S+/www\.youtube\.com/\S+/|watch\?feature=youtu.be&v=)([^&%#\n?]+)'

    # Use the regular expression to find the video ID
    match = re.search(pattern, url)

    if match:
        video_id = match.group(1)
        return video_id
    else:
        return None

#################################################
# Defining a function to get the video captions #
#################################################
# Importing relevant libraries
from youtube_transcript_api import YouTubeTranscriptApi

@app.route('/get_captions', methods=['POST'])
def get_captions(video_id):
    captions_ts = []
    captions = []
    try:
        video_transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # Print the captions
        for caption in video_transcript:
            start = caption['start']
            end = caption['start'] + caption['duration']
            text = caption['text']
            caption = f"Timestamp: {start:.2f} - {end:.2f}\n{text}\n"
            captions_ts.append(caption)
            captions.append(text)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    # Convert Captions to strings
    captions_str = '\n'.join(captions)

    return captions

################################
# User input for YouTube video #
################################
video_url = input('Please Enter your YouTube video of interest: ')

#####################################
# Getting the YouTube video details #
#####################################
yt = YouTube(video_url)
video_id = get_video_id(video_url)

# Get video details
yt = YouTube(video_url)
video_id = get_video_id(video_url)
video_response = youtube.videos().list(
    part = 'snippet, contentDetails',
    id = video_id
    ).execute()

# Extract relevant information from the response
video_info = video_response['items'][0]
video_snippet = video_info['snippet']
video_content_details = video_info['contentDetails']

# Get video title
video_title = video_snippet['title']

# Get video length in seconds
video_duration = video_content_details['duration']

# Get video creator (channel name)
video_creator = video_snippet['channelTitle']

# Get date uploaded
date_uploaded = video_snippet['publishedAt']

# Print or use the retrieved information
print(f'Video ID: {video_id}')
print(f"Video Title: {video_title}")
print(f"Video Length (seconds): {video_duration}")
print(f"Video Creator: {video_creator}")
print(f"Date Uploaded: {date_uploaded}")

# Getting the current date and time 
date_updated = datetime.datetime.now()
date_updated = date_updated.strftime('%Y-%m-%d %H:%M:%S')



#########################################
# Asking OpenAI for summary information #
#########################################
# Creating a prompt to summarize the video
captions = get_captions(video_id)
prompt = f'Summarize this video with the following words spoken:\n {captions}'

# Send the prompt to be summarized
response = openai.ChatCompletion.create(
    model = 'gpt-3.5-turbo',
    messages = [
        {"role": "system", "content": "You are a summarization helpful assistant."},
        {"role": "user", "content": prompt}
    ]
)

# Extract a summary from the response
summary = response['choices'][0]['message']['content']

# Printing out the summary
print('Generated Summary:')
print(summary)

# Running the Flask Instance
if __name__ == '__main__':
    app.run(debug=True)
