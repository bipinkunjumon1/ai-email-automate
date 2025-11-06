from gmail_service import get_latest_unread_email, send_email
from ai_agent import generate_reply
from db_service import insert_record, init_db

def main():
    print("🔍 Reading latest email...")
    sender, subject, email_text = get_latest_unread_email()

    if not sender:
        print("📭 No new emails.")
        return

    print(f"📥 New email from: {sender}")
    print(f"📌 Subject: {subject}")

    print("🤖 Processing with AI agent...")
    reply_text, all_ok, details, ignored = generate_reply(email_text, subject)

    # 🛑 Skip vendor emails
    if ignored:
        print("🚫 Ignored vendor email — no action taken.")
        return

    # ✉️ Send AI reply to customer
    send_email(sender, f"Re: {subject}", reply_text)
    print("✅ Reply sent successfully.")

    # 💾 Save in database
    insert_record(
        sender,
        email_text,
        reply_text,
        details.get("product_name"),
        details.get("price"),
        details.get("quantity"),
        all_ok
    )

    print("💾 Record saved in database.")

if __name__ == "__main__":
    init_db()
    main()