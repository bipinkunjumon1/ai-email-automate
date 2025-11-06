# gmail_service.py
import base64
import os.path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import google.auth.transport.requests

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def get_gmail_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("gmail", "v1", credentials=creds)
    return service

def get_latest_unread_email():
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", labelIds=["INBOX", "UNREAD"], maxResults=5).execute()
    messages = results.get("messages", [])
    if not messages:
        return None, None, None

    msg = service.users().messages().get(userId="me", id=messages[0]["id"]).execute()
    headers = msg["payload"]["headers"]
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "")
    body_data = msg["payload"]["parts"][0]["body"].get("data", "")
    body = base64.urlsafe_b64decode(body_data).decode("utf-8")

    # mark as read
    service.users().messages().modify(
        userId="me",
        id=messages[0]["id"],
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()

    return sender, subject, body


def send_email(to, subject, body):
    service = get_gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}

    send_message = (
        service.users().messages().send(userId="me", body=create_message).execute()
    )
    return send_message