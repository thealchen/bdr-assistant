import os
import base64
from typing import Optional
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.compose']


class GmailAPI:
    """Gmail API client for creating draft emails."""

    def __init__(self):
        self.credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
        self.service = None

    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found at {self.credentials_path}. "
                        "Download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def create_draft(self, to: str, subject: str, body: str) -> Optional[str]:
        """Create a draft email in Gmail.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)

        Returns:
            Draft ID if successful, None otherwise
        """
        try:
            if not self.service:
                self._authenticate()

            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={
                    'message': {
                        'raw': raw_message
                    }
                }
            ).execute()

            return draft.get('id')

        except FileNotFoundError as e:
            print(f"Gmail API setup required: {e}")
            return None
        except Exception as e:
            print(f"Failed to create Gmail draft: {e}")
            return None
