from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build

# 必要なYouTube APIのスコープ（高評価動画の読み取り権限）
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# oauth
def get_authenticated_service():
   flow = InstalledAppFlow.from_client_secrets_file('client_secret_989428469834-i53pujjk47rpq01p8hh9kp0irhursjoj.apps.googleusercontent.com.json', SCOPES)
   credentials = flow.run_local_server(port=8081)
   return build('youtube', 'v3', credentials=credentials)

 # 高評価動画を取得
def get_liked_videos(youtube):
   request = youtube.videos().list(
       part="snippet",
       myRating="like",
       maxResults=10
   )
   response = request.execute()
   return response.get("items", [])