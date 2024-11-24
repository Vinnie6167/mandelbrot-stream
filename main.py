import os

from PIL import Image
import numpy as np
import cv2
import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import matplotlib.pyplot as plt


def mandelbrot(c, max_iter):
  """Calculates whether a complex number belongs to the Mandelbrot set."""
  z = 0
  n = 0
  while abs(z) <= 2 and n < max_iter:
    z = z*z + c
    n += 1
  return n

def create_mandelbrot_image(width, height, center_x, center_y, zoom, max_iter):
  """Creates an image of the Mandelbrot set."""
  x, y = np.mgrid[-width/2:width/2, -height/2:height/2]
  x = (x / zoom + center_x) * 2.5 / width - 2.0
  y = (y / zoom + center_y) * 2.5 / height - 1.25
  c = x + 1j * y
  mandelbrot_set = np.frompyfunc(mandelbrot, 2, 1)(c, max_iter).astype(float)

  # **Map the Mandelbrot set to colors:**
  escaped_ratio = mandelbrot_set / max_iter 
  # Use a colormap (you can experiment with different ones)
  colors = plt.cm.viridis(escaped_ratio) 
  colors = (colors[:, :, :3] * 255).astype(np.uint8) # Convert to RGB values

  # **Create a PIL Image:**
  image = Image.fromarray(colors) 
  return image

# --- YouTube Live Streaming ---

# **1. YouTube API Setup:**
#   * You'll need a Google Cloud Project with the YouTube Data API v3 enabled.
#   * Create OAuth 2.0 credentials and download the `client_secrets.json` file.
#   * Replace 'YOUR_CLIENT_SECRET_FILE' and 'YOUR_OAUTH_SCOPE' below.

CLIENT_SECRETS_FILE = os.environ.get('CLIENT_SECRETS_PATH')
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
DEBUG = True

def get_authenticated_service():
  """Authorizes the request and returns the YouTube service."""
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
      token.write(creds.to_json())
  
  return build('youtube', 'v3', credentials=creds)

def start_live_stream(service, stream_title, stream_description):
  if DEBUG:
    return

  """Creates and starts a live stream on YouTube."""
  request = service.liveStreams().insert(
    part="snippet,cdn,contentDetails,status",
    body={
      "snippet": {
        "title": stream_title,
        "description": stream_description
      },
      "cdn": {
        "frameRate": "60fps",
        "resolution": "1080p",
        "ingestionType": "rtmp"
      },
      "contentDetails": {
        "isReusable": True
      },
      "status": {
        "streamStatus": "active", 
        "privacyStatus": "public" 
      }
    }
  )
  response = request.execute()
  return response

# **2. Streaming with OpenCV:**
def stream_to_youtube(service, stream_key):
  width, height = 192, 108
  center_x, center_y = -0.75, 0 
  zoom = 1
  max_iter = 255

  """Streams the Mandelbrot frames to YouTube Live."""
  # Use OpenCV to encode and stream video
  if DEBUG:
    out = cv2.VideoWriter(
      'mandelbrot_stream.mp4', 
      cv2.VideoWriter_fourcc(*'mp4v'), 
      60, # Frames per second
      (width, height)
    ) 
  else:
    # Get RTMP URL and stream key from the live stream response
    rtmp_url = service.liveStreams().list(
      part="cdn",
      id=stream_id
    ).execute()['items'][0]['cdn']['ingestionInfo']['ingestionAddress'] + '/' + stream_key
    out = cv2.VideoWriter(
      rtmp_url, 
      cv2.VideoWriter_fourcc(*'avc1'), 
      60, # Frames per second
      (width, height) 
    )

  frame_count = 0
  while True:
    # Generate Mandelbrot frame
    image = create_mandelbrot_image(width, height, center_x, center_y, zoom, max_iter) 
    frame = np.array(image) # Convert PIL Image to NumPy array
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to BGR for OpenCV

    # Write the frame to the stream
    out.write(frame)
    frame_count += 1
    print(frame_count)

    # ... (Code to update center_x, center_y, and zoom for animation)

    if DEBUG and frame_count > 60:
      break
  
  out.release()

if __name__ == "__main__":
  # --- Set up the stream ---
  service = get_authenticated_service()
  stream_title = "Endless Mandelbrot Zoom"
  stream_description = "A mesmerizing journey through the Mandelbrot set."
  if not DEBUG:
    live_stream = start_live_stream(service, stream_title, stream_description)
    stream_id = live_stream['id']
    stream_key = live_stream['cdn']['ingestionInfo']['streamName']

    # --- Start the stream ---
    stream_to_youtube(service, stream_key)

  else:
    stream_to_youtube(None, None)