import os
import base64
import json
from typing import Optional, Type
from email.mime.text import MIMEText
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
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


class GmailDraftInput(BaseModel):
    """Input schema for Gmail draft tool."""
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content (plain text)")


class GmailDraftTool(BaseTool):
    """LangChain tool for creating Gmail draft emails."""

    name: str = "gmail_draft"
    description: str = "Create a draft email in Gmail. Returns the draft ID if successful."
    args_schema: Type[BaseModel] = GmailDraftInput

    gmail_api: Optional[GmailAPI] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gmail_api = GmailAPI()

    def _run(self, to: str, subject: str, body: str) -> str:
        """Create a draft email in Gmail.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)

        Returns:
            JSON string with draft_id if successful, error otherwise
        """
        draft_id = self.gmail_api.create_draft(to=to, subject=subject, body=body)

        if draft_id:
            result = {
                "success": True,
                "draft_id": draft_id,
                "message": f"Draft created successfully for {to}"
            }
        else:
            result = {
                "success": False,
                "draft_id": None,
                "message": "Failed to create Gmail draft"
            }

        return json.dumps(result)
