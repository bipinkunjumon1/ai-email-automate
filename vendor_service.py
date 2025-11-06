from gmail_service import send_email

def send_vendor_email(
    vendor_email,
    product_name=None,
    price=None,
    quantity=None,
    order_id=None,
    query_type="order",
    vendor_message=None
):
    """
    Sends an email to the vendor based on the customer's query type.
    Handles missing or invalid numeric fields gracefully.
    """

    def safe_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def safe_int(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    # --- ORDER REQUEST ---
    if query_type == "order":
        subject = f"New Order Received: {product_name or 'Unknown Product'} (Order ID: {order_id or 'N/A'})"

        if vendor_message:
            body = vendor_message
        else:
            price_val = safe_float(price)
            qty_val = safe_int(quantity)
            total = price_val * qty_val
            shipping = 50 if total > 0 else 0
            total_cost = total + shipping

            body = f"""
Dear Vendor,

A new order has been placed. Please process the shipment with the following details:

- Product: {product_name or 'Not specified'}
- Quantity: {quantity or 'Not specified'}
- Price per unit: ₹{price or 'Not specified'}
- Shipping charge: ₹{shipping}
- Total cost: ₹{total_cost}

Please attach at least 2 food safety certificates with the shipment confirmation email.

Best regards,  
AI Order Management Assistant
"""

    # --- SHIPPING QUERY ---
    elif query_type == "shipping":
        subject = f"Shipping Status Request for Order ID: {order_id or 'N/A'}"
        body = vendor_message or f"""
Dear Vendor,

The customer has inquired about the shipping status for Order ID {order_id or 'N/A'}.
Kindly provide the latest shipment update (e.g., dispatched, in transit, delivered).

Please attach shipment proof if available.

Best regards,  
AI Shipping Assistant
"""

    # --- DEFAULT FALLBACK ---
    else:
        subject = "Vendor Communication"
        body = vendor_message or "This is an automated message from the AI assistant."

    # Send the email
    send_email(vendor_email, subject, body)
    print(f"✅ Vendor email sent successfully: {subject}")
