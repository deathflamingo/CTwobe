import os
import httplib2
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request # Corrected import


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Cloud Console at https://cloud.google.com/console.
# Please ensure that you have enabled the YouTube Data API for your project.
CLIENT_SECRETS_FILE = 'client_secret.json'

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's YouTube account.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# The VALID_PRIVACY_STATUSES list defines the privacy statuses that YouTube
# supports and that the script will accept as input.
VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')

def get_authenticated_service():
    """Authenticate and return the YouTube API service."""
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            # Use the allows_non_optionary_args=True to handle potential command line args
            # passed to the script that are not specifically for the flow.
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def initialize_upload(youtube, options):
    """Initialize the upload process."""
    tags = None
    if options['keywords']:
        tags = options['keywords'].split(',')

    body = dict(
        snippet=dict(
            title=options['title'],
            description=options['description'],
            tags=tags,
            categoryId=options['category']
        ),
        status=dict(
            privacyStatus=options['privacyStatus']
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting 'chunksize' equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options['file'], chunksize=-1, resumable=True)
    )

    return resumable_upload(insert_request)

def resumable_upload(request):
    """Upload the video file using resumable upload."""
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print('Uploading file...')
            status, response = request.next_chunk()
            if status:
                print(f'Uploaded {int(status.progress() * 100)}%')
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                error = f'Upload failed: %s' % e.content
                print(error)
                retry += 1
                if retry > 5: # Limit retries
                    raise
                print(f'Retrying upload in {2**retry} seconds...')
                import time
                time.sleep(2**retry)
            else:
                raise
        except Exception as e:
            error = f'An upload error occurred: {e}'
            print(error)
            raise

    if 'id' in response:
        print(f'Video id "{response["id"]}" was successfully uploaded.')
        return response['id']
    else:
        exit(f'The upload failed with an unexpected response: {response}')

if __name__ == '__main__':
    # This example uses a dictionary for options, you could use argparse for
    # command-line arguments in a real application.
    video_options = {
        'file': 'video1.mp4', # <== Change this to your video file path
        'title': 'My Awesome Video Upload', # <== Change this to your video title
        'description': 'This video was uploaded using the YouTube Data API.', # <== Change this to your video description
        'category': '22', # <== Change this to a valid YouTube category ID (22 is People & Blogs)
        'keywords': 'python, youtube api, upload', # <== Change this to your video keywords (comma-separated)
        'privacyStatus': 'private' # <== Change to 'public', 'unlisted', or 'private'
    }

    if not os.path.exists(video_options['file']):
        exit(f'Please specify a valid file using the "file" option in the script.')

    if video_options['privacyStatus'] not in VALID_PRIVACY_STATUSES:
        exit(f'Please specify a valid privacyStatus from: {", ".join(VALID_PRIVACY_STATUSES)}')

    youtube = get_authenticated_service()

    try:
        video_id = initialize_upload(youtube, video_options)
        print(f'Video uploaded successfully! Video ID: {video_id}')
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')
    except Exception as e:
        print(f'An error occurred: {e}')