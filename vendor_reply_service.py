import base64
import re
import os
import time
from gmail_service import get_gmail_service, send_email
from db_service import update_vendor_reply

ATTACHMENTS_DIR = "vendor_attachments"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)


def read_vendor_emails():
    print("📩 Checking Gmail inbox for vendor shipment updates...")
    service = get_gmail_service()

    try:
        results = service.users().messages().list(
            userId="me", labelIds=["INBOX", "UNREAD"], maxResults=20
        ).execute()
    except Exception as e:
        print("❌ Failed to connect to Gmail:", e)
        return

    messages = results.get("messages", [])
    if not messages:
        print("📭 No new vendor emails found.")
        return

    for msg in messages:
        try:
            data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        except Exception as e:
            print("⚠️ Skipping message (failed to fetch):", e)
            continue

        headers = data.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")

        # Only process emails containing 'vendor'
        if "vendor" not in subject.lower():
            continue

        # Extract body
        payload = data.get("payload", {})
        body_data = ""

        def extract_body(payload_part):
            if not payload_part:
                return ""
            if payload_part.get("mimeType") == "text/plain":
                return payload_part.get("body", {}).get("data", "")
            if "parts" in payload_part:
                for p in payload_part["parts"]:
                    result = extract_body(p)
                    if result:
                        return result
            return payload_part.get("body", {}).get("data", "")

        body_data = extract_body(payload)
        try:
            body = base64.urlsafe_b64decode(body_data).decode("utf-8")
        except Exception:
            body = "(Unable to decode body)"

        print(f"\n📨 Vendor Email from: {sender}")
        print(f"📌 Subject: {subject}")
        print(f"📝 Body excerpt: {body[:300]}...\n")

        # Extract shipment & payment info
        shipped_match = re.search(r"(shipped|dispatched|delivered|not\s+shipped|confirmed|dispatch)", body, re.I)
        payment_match = re.search(r"(?:payment|amount)[:\- ]*₹?\s?(\d+[,.]?\d*)", body, re.I)

        vendor_status = shipped_match.group(1).capitalize() if shipped_match else "Pending"
        payment_amount = payment_match.group(1) if payment_match else "N/A"

        # Download PDF attachments
        pdf_paths = []

        def download_attachments(part, msg_id):
            if not part:
                return
            if part.get("filename"):
                filename = part.get("filename")
                if filename.lower().endswith(".pdf"):
                    attach_id = part.get("body", {}).get("attachmentId")
                    if attach_id:
                        try:
                            attachment = service.users().messages().attachments().get(
                                userId="me", messageId=msg_id, id=attach_id
                            ).execute()
                            data = attachment.get("data")
                            file_data = base64.urlsafe_b64decode(data.encode("UTF-8"))
                            base_name = _safe_filename(sender.split("<")[0]) or "vendor"
                            ts = int(time.time())
                            safe_name = f"{base_name}_{ts}_{_safe_filename(filename)}"
                            file_path = os.path.join(ATTACHMENTS_DIR, safe_name)
                            with open(file_path, "wb") as f:
                                f.write(file_data)
                            pdf_paths.append(file_path)
                        except Exception as e:
                            print("⚠️ Failed to download attachment:", e)
            # recurse into parts
            for p in part.get("parts", []) if part.get("parts") else []:
                download_attachments(p, msg_id)

        download_attachments(payload, msg["id"])
        pdf_count = len(pdf_paths)
        print(f"📎 Found {pdf_count} PDF attachment(s): {pdf_paths}")

        # Require at least 2 PDFs
        if pdf_count < 2:
            print("⚠️ Vendor did not attach enough certificates. Sending reminder...")
            reminder_body = f"""Dear Vendor,

We received your shipment update for "{subject}", but only {pdf_count} certificate(s) were attached.
Please resend with at least **2 valid PDFs**.

Best regards,
AI Shipping Manager
"""
            try:
                send_email(sender, f"Re: {subject} - Missing Certificates", reminder_body)
                print(f" Sent reminder to vendor: {sender}")
            except Exception as e:
                print("⚠️ Failed to send reminder email:", e)
            # Mark as read
            try:
                service.users().messages().modify(
                    userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}
                ).execute()
            except Exception:
                pass
            continue

        # ✅ Update DB for vendor record
        pdf1 = pdf_paths[0] if len(pdf_paths) > 0 else None
        pdf2 = pdf_paths[1] if len(pdf_paths) > 1 else None

        # Normalize sender email
        sender_email_only = re.search(r"<(.+?)>", sender)
        sender_email_only = sender_email_only.group(1) if sender_email_only else sender.strip()

        try:
            # Updated: create new record if none exists
            update_vendor_reply(
                sender_email_only,
                vendor_status,
                payment_amount,
                pdf1_path=pdf1,
                pdf2_path=pdf2,
                vendor_email=sender_email_only  # Ensure vendor_email column is updated
            )
            print(f"✅ Database updated for {sender_email_only}: status={vendor_status}, payment={payment_amount}")
        except Exception as e:
            print("⚠️ DB update failed:", e)

        # Send acknowledgment
        ack_body = f"""Dear Vendor,

Thank you — we received your shipment confirmation and attached certificates.

📦 Shipment Status: {vendor_status}
💰 Payment amount: ₹{payment_amount or 'N/A'}
📄 Certificates received: {pdf_count}

The manager will review the certificates and update the customer soon.

Best regards,
AI Shipping Manager
"""
        try:
            send_email(sender, f"Acknowledgment — {subject}", ack_body)
            print(f"✉️ Acknowledgment sent to vendor: {sender}")
        except Exception as e:
            print("⚠️ Failed to send acknowledgment email:", e)

        # Mark email as read
        try:
            service.users().messages().modify(
                userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}
            ).execute()
        except Exception:
            pass

    print("\n🎯 All vendor updates processed.")


if __name__ == "__main__":
    read_vendor_emails()