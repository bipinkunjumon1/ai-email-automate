import re
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from gmail_service import send_email  # ✅ For Gmail replies

# --------------------------------------------
# Load environment variables
# --------------------------------------------
load_dotenv()

# ✅ Configure Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY") or "YOUR_API_KEY_HERE"
)

# --------------------------------------------
# Prompt Template
# --------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI email assistant for a food product shipping company."),
    ("human", """
Analyze the following customer email carefully.

Customer Email:
{email_text}

1️⃣ Determine if this is:
   - a new order request, or
   - a shipping/delivery query.
2️⃣ Extract Order ID, Product Name, Product Price, and Quantity.
3️⃣ If order details are missing, politely ask for the missing information.
4️⃣ If it’s a shipping query, reply appropriately (that you’ll check with vendor).
5️⃣ Keep the reply short, polite, and professional.
6️⃣ Return only the reply text (no explanation).
""")
])

chain = prompt | model


# -------------------------------------------------
# FUNCTION: Analyze and respond to customer emails
# -------------------------------------------------
def generate_reply(email_text: str, subject: str = "") -> tuple[str, bool, dict, bool]:
    """
    Analyze incoming email using Gemini + regex.
    Returns: (reply_text, all_details_collected, details_dict, ignored)
    """

    # 🛑 Ignore vendor-related mails
    if "vendor" in subject.lower():
        print("⚠️ Ignored vendor email based on subject content.")
        return None, False, {}, True

    # 🧠 Extract structured data
    details = {
        "order_id": None,
        "product_name": None,
        "price": None,
        "quantity": None,
        "query_type": "order"  # default assumption
    }

    # ✅ Improved Regex Patterns
    order_id_match = re.search(r'(?i)(?:order[\s_-]*(?:id)?[\s#:=-]*)(\d{2,})', email_text)
    product_match = re.search(r'(?i)(?:product\s*(?:name)?[:\- ]*)([A-Za-z0-9\s]+)', email_text)
    price_match = re.search(r'(?i)(?:price|cost)[:\- ]*₹?\s?(\d+[,.]?\d*)', email_text)
    quantity_match = re.search(r'(?i)(?:quantity|qty|pieces|units|packs)[:\- ]*(\d+)', email_text)

    if order_id_match:
        details["order_id"] = order_id_match.group(1).strip()
    if product_match:
        details["product_name"] = product_match.group(1).strip()
    if price_match:
        details["price"] = price_match.group(1).strip()
    if quantity_match:
        details["quantity"] = quantity_match.group(1).strip()

    # ✅ Detect shipping-related keywords
    shipping_keywords = [
        "delivery", "ship", "shipping", "status", "dispatched", "arrive", "track", "tracking",
        "where is my order", "delivered", "dispatch", "when will"
    ]
    email_lower = email_text.lower()
    is_shipping_query = any(keyword in email_lower for keyword in shipping_keywords)

    if is_shipping_query:
        details["query_type"] = "shipping"

    # ✅ Validate completeness for orders
    all_details_collected = bool(details["order_id"] and details["product_name"])

    # 🗣️ Generate reply
    if is_shipping_query:
        # --- SHIPPING QUERY HANDLING ---
        if details["order_id"]:
            reply_text = (
                f"Dear Customer,\n\n"
                f"Thank you for reaching out. We’ve received your shipping enquiry "
                f"for Order ID {details['order_id']}. We will check with the vendor "
                f"and update you shortly.\n\n"
                f"Best regards,\nAI Shipping Assistant"
            )
        else:
            reply_text = (
                f"Dear Customer,\n\n"
                f"Could you please provide your Order ID so we can check your delivery status?\n\n"
                f"Thank you,\nAI Shipping Assistant"
            )

    else:
        # --- NEW ORDER HANDLING ---
        if not all_details_collected:
            missing_parts = []
            if not details["order_id"]:
                missing_parts.append("Order ID")
            if not details["product_name"]:
                missing_parts.append("Product Name")

            missing_text = " and ".join(missing_parts)
            reply_text = (
                f"Dear Customer,\n\n"
                f"We couldn’t locate your {missing_text} in the email. "
                f"Kindly share these details to help us process your request.\n\n"
                f"Thank you,\nAI Order Assistant"
            )
        else:
            reply_text = (
                f"Dear Customer,\n\n"
                f"Thank you for reaching out. We have received your query regarding "
                f"Order #{details['order_id']} for product '{details['product_name']}'. "
                f"Our manager will review and process it shortly.\n\n"
                f"Best regards,\nAI Order Assistant"
            )

    print("🧩 Extracted Details:", details)
    print("🚚 Is Shipping Query:", is_shipping_query)
    return reply_text, all_details_collected, details, False


# -------------------------------------------------
# FUNCTION: Send shipment/payment update to customer
# -------------------------------------------------
def send_customer_update(customer_email, vendor_status, payment_amount, approved=True):
    if approved:
        subject = "Your Order Update – Product Shipment Confirmed"
        body = f"""
Dear Customer,

Good news! The vendor has confirmed your product shipment.

📦 Status: {vendor_status}
💰 Payment Amount: ₹{payment_amount or 'N/A'}

Thank you for shopping with us!
Best regards,  
AI Shipping Assistant
        """
    else:
        subject = "Your Order Update – Shipment Rejected"
        body = f"""
Dear Customer,

Unfortunately, your order could not be shipped due to vendor unavailability.

📦 Status: {vendor_status or 'Not Shipped'}
💰 Refund Amount: ₹{payment_amount or 'N/A'}

We apologize for the inconvenience.
Best regards,  
AI Shipping Assistant
        """

    send_email(customer_email, subject, body)
    print(f"✅ Sent update email to customer: {customer_email}")


# -------------------------------------------------
# Local Test
# -------------------------------------------------
if __name__ == "__main__":
    print("\n🧪 TEST 1 — ORDER MAIL\n")
    order_email = """
    Hello,

    I’d like to place an order for Product: Organic Oats.
    Quantity: 5 packs
    Price: ₹350 each
    Order ID- 5678

    Please confirm if this product is available and the expected delivery time.

    Thank you,
    Arjun
    """
    reply, ok, det, ignored = generate_reply(order_email, subject="Order Request")
    if not ignored:
        print("🤖 AI Reply:\n", reply)
        print("🧩 Extracted Details:", det)

    print("\n🧪 TEST 2 — SHIPPING MAIL\n")
    shipping_email = """
    Hi Team,
    When will my Order ID 5678 be delivered? I ordered it last week and haven’t received any update.
    Thanks,
    Arjun
    """
    reply, ok, det, ignored = generate_reply(shipping_email, subject="Delivery Status")
    if not ignored:
        print("🤖 AI Reply:\n", reply)
        print("🧩 Extracted Details:", det)