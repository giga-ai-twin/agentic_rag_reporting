import os
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime

from streamlit import title

class SlideGenerator:
    """
    Automates the creation of Google Slides presentations.
    """
    SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']
    INSTALL_ACCOUNT_FILE = 'local_service_account.json'
    SERVICE_ACCOUNT_FILE = 'service_account.json'

    def __init__(self):
        # Verify if the credentials exist

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        try:
            # Load existing credentials if available
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.INSTALL_ACCOUNT_FILE, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            # Use service account credentials for server-to-server interactions
            self.slides_service = build('slides', 'v1', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            print("✅ [Init] Services built successfully.") # [Debug]

        except Exception as e:
            print(f"❌ [Init] Failed to build services: {e}")
            raise e

    def _hex_to_rgb(self, hex_color):
        """
        Converts HEX string (e.g., '#4a86e8') to Google Slides RGB dictionary.
        """
        hex_color = hex_color.lstrip('#')
        return {
            'red': int(hex_color[0:2], 16) / 255.0,
            'green': int(hex_color[2:4], 16) / 255.0,
            'blue': int(hex_color[4:6], 16) / 255.0
        }

    def _clean_text(self, text):
        """
        Removes HTML tags and Markdown syntax for cleaner slide output.
        """
        if not text: return ""
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)

        return text.strip()

    def create_presentation(self, title):
        try:
            """Creates a new presentation and returns its ID and URL."""
            body = {'title': title}
            presentation = self.slides_service.presentations().create(body=body).execute()
            presentation_id = presentation.get('presentationId')
            print(f"Created presentation with ID: {presentation_id}")

            TITLE_STYLE = {
                'fontFamily': 'Google Sans Flex',
                'fontSize': {'magnitude': 38, 'unit': 'PT'},
                'bold': False,
                'color': self._hex_to_rgb('#1a73e8')
            }

            SUB_TITLE_STYLE = {
                'fontFamily': 'Google Sans Flex',
                'fontSize': {'magnitude': 18, 'unit': 'PT'},
                'bold': False,
                'color': self._hex_to_rgb("#535353")
            }

            # Obtain the first cover slide.
            first_slide = presentation.get('slides')[0]

            # Find the placeholder IDs for "Title" and "Subtitle".
            title_object_id = None
            subtitle_object_id = None

            # Iterate through all elements on the first page and find the title box.
            for element in first_slide.get('pageElements', []):
                shape = element.get('shape')
                if not shape: continue

                placeholder = shape.get('placeholder')
                if not placeholder: continue

                type_ = placeholder.get('type')
                if type_ in ['CENTERED_TITLE', 'TITLE']:
                    title_object_id = element.get('objectId')
                elif type_ == 'SUBTITLE':
                    subtitle_object_id = element.get('objectId')

            # Prepare requests to fill in the title and subtitle.
            requests = []

            # Fill in the title
            if title_object_id:
                requests.append({
                    'insertText': {
                        'objectId': title_object_id,
                        'text': title
                    }
                })
                requests.append({
                    'updateTextStyle': {
                        'objectId': title_object_id,
                        'style': {
                            'weightedFontFamily': {'fontFamily': TITLE_STYLE['fontFamily']},
                            'fontSize': TITLE_STYLE['fontSize'],
                            'bold': TITLE_STYLE['bold'],
                            'foregroundColor': {
                                'opaqueColor': {
                                    'rgbColor': TITLE_STYLE['color']
                                }
                            }
                        },
                        'fields': 'weightedFontFamily,fontSize,bold,foregroundColor'
                    }
                })

            # Fill in the subtitle with current timestamp
            if subtitle_object_id:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                requests.append({
                    'insertText': {
                        'objectId': subtitle_object_id,
                        'text': f"Generated by AI Agent at {current_time}"
                    }
                })
                requests.append({
                    'updateTextStyle': {
                        'objectId': subtitle_object_id,
                        'style': {
                            'weightedFontFamily': {'fontFamily': SUB_TITLE_STYLE['fontFamily']},
                            'fontSize': SUB_TITLE_STYLE['fontSize'],
                            'bold': SUB_TITLE_STYLE['bold'],
                            'foregroundColor': {
                                'opaqueColor': {
                                    'rgbColor': SUB_TITLE_STYLE['color']
                                }
                            }
                        },
                        'fields': 'weightedFontFamily,fontSize,bold,foregroundColor'
                    }
                })

            # Execute the requests to update the presentation
            if requests:
                self.slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()


            # Set permissions to allow anyone to read the data for demo purposes ONLY
            # TODO: For production environments have to use email invitations instead
            self._share_file(presentation_id)

            return presentation_id, f"https://docs.google.com/presentation/d/{presentation_id}"

        except HttpError as err:
            print(f"❌ [Step 1] Google API Error: {err}")
            if err.resp.get('content'):
                print(f"   Details: {err.resp.content}")
            raise err

    def _share_file(self, file_id):
        """Shares the file so you can open it without logging into the service account."""
        try:
            batch = self.drive_service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'writer'},
                fields='id',
            ).execute()
            print("✅ [Step 1.5] Share success.")
        except HttpError as err:
            print(f"⚠️ [Step 1.5] Share Warning: {err}")

    def add_summary_slide(self, presentation_id, slide_title, long_text):
        """
        [Smart Split] Automatically splits long text into multiple slides.
        Optimized to prevent empty slides and utilize space better.
        """
        long_text = self._clean_text(long_text)

        MAX_CHARS = 750

        paragraphs = long_text.split('\n')
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            if not p.strip():
                continue

            if len(current_chunk) + len(p) < MAX_CHARS:
                current_chunk += p + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = p + "\n"
                else:
                    chunks.append(p + "\n")
                    current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk)

        print(f"📄 Content split into {len(chunks)} slides.")

        for i, chunk in enumerate(chunks):
            if len(chunks) > 1:
                current_title = f"{slide_title} ({i+1}/{len(chunks)})"
            else:
                current_title = slide_title

            self._create_single_slide(presentation_id, current_title, chunk)

    def _create_single_slide(self, presentation_id, title, content):
        """
        Internal method to create one single slide.
        (This contains the original logic)
        """
        TITLE_STYLE = {
            'fontFamily': 'Google Sans Flex',
            'fontSize': {'magnitude': 24, 'unit': 'PT'},
            'bold': False,
            'color': self._hex_to_rgb("#000000")
        }

        CONTENT_STYLE = {
            'fontFamily': 'Google Sans Flex',
            'fontSize': {'magnitude': 10, 'unit': 'PT'},
            'bold': False,
            'color': self._hex_to_rgb("#303030")
        }

        try:
            print(f"   -> Creating slide: {title}...")
            # 1. Create a new slide
            requests = [
                {
                    'createSlide': {
                        'slideLayoutReference': {'predefinedLayout': 'TITLE_AND_BODY'}
                    }
                }
            ]

            body = {'requests': requests}
            response = self.slides_service.presentations().batchUpdate(
                presentationId=presentation_id, body=body).execute()

            slide_id = response['replies'][0]['createSlide']['objectId']

            # 2. Get Placeholders
            slide = self.slides_service.presentations().pages().get(
                presentationId=presentation_id, pageObjectId=slide_id).execute()

            title_id = None
            body_id = None

            for element in slide.get('pageElements', []):
                if 'shape' in element and 'placeholder' in element['shape']:
                    type_ = element['shape']['placeholder']['type']
                    if type_ == 'TITLE':
                        title_id = element['objectId']
                    elif type_ == 'BODY':
                        body_id = element['objectId']

            # 3. Insert Text
            text_requests = []
            if title_id:
                text_requests.append({'insertText': {'objectId': title_id, 'text': title}})
                text_requests.append({'updateTextStyle': {
                    'objectId': title_id,
                    'style': {
                                'weightedFontFamily': {'fontFamily': TITLE_STYLE['fontFamily']},
                                'fontSize': TITLE_STYLE['fontSize'],
                                'bold': TITLE_STYLE['bold'],
                                'foregroundColor': {
                                  'opaqueColor': {
                                      'rgbColor': TITLE_STYLE['color']
                                  }
                                }
                              },
                    'fields': '*'
                    }})

            if body_id:
                text_requests.append({'insertText': {'objectId': body_id, 'text': content}})
                text_requests.append({'updateTextStyle': {
                    'objectId': body_id,
                    'style': {'weightedFontFamily': {'fontFamily': CONTENT_STYLE['fontFamily']},
                              'fontSize': CONTENT_STYLE['fontSize'],
                              'bold': CONTENT_STYLE['bold'],
                              'foregroundColor': {
                                  'opaqueColor': {
                                      'rgbColor': CONTENT_STYLE['color']
                                  }
                                }
                            },
                    'fields': '*'
                    }})

            if text_requests:
                self.slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': text_requests}
                ).execute()

        except Exception as e:
            print(f"❌ Failed to create slide '{title}': {e}")

# Test locally
if __name__ == "__main__":
    try:
        gen = SlideGenerator()
        pid, url = gen.create_presentation("Giga Factory Daily Report")
        gen.add_summary_slide(pid, "Executive Summary", "1. Yield rate is stable.\n2. BMS Issue detected in v2.1.0.")
        print(f"Success! Open here: {url}")
    except Exception as e:
        print(f"Error: {e}")