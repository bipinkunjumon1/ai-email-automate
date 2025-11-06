import streamlit as st 
import os
import re
from db_service import (
    get_all_records,
    mark_as_approved,
    update_manager_decision,
    get_pending_vendor_updates
)
from vendor_service import send_vendor_email
from ai_agent import send_customer_update, generate_reply
from gmail_service import send_email  


# Streamlit Page Setup
st.set_page_config(page_title="AI Email Agent", page_icon="📦", layout="wide")
st.title("📧 AI Email Agent – Manager Dashboard")


# SECTION 1: Customer Emails 
records = get_all_records()

if not records:
    st.info("📭 No email records found yet. Run main.py first to process customer emails.")
else:
    st.subheader("📬 Processed Customer Emails (Pending Vendor Action)")

    for record in records:
        (
            record_id,
            sender_email,
            email_text,
            reply_text,
            product_name,
            price,
            quantity,
            ready_for_approval,
            approved,
            vendor_status,
            payment_amount,
            manager_decision,
            vendor_pdf1,
            vendor_pdf2,
            vendor_email,
            *rest  
        ) = tuple(record) + (None,) * (15 - len(record))

        with st.expander(f"📨 Customer: {sender_email} — Record #{record_id}"):
            # DISPLAY CUSTOMER DETAILS 
            st.markdown("### 🧾 Customer Email")
            st.write(email_text)

            st.markdown("### 🤖 AI Reply Sent to Customer")
            st.write(reply_text)

            st.markdown("### 📦 Product Details")
            st.write(f"- **Product:** {product_name or '❌ Missing'}")
            st.write(f"- **Price:** ₹{price or '❌ Missing'}")
            st.write(f"- **Quantity:** {quantity or '❌ Missing'}")

            # MANAGER ACTIONS 
            if approved:
                st.success("✅ Already approved and vendor has been notified.")
            else:
                st.warning("⚠️ Awaiting manager action.")
                _, _, details, is_shipping_query = generate_reply(email_text, subject="")

                with st.form(f"approve_form_{record_id}"):
                    vendor_email_input = st.text_input("Vendor Email", value=vendor_email or "", key=f"vendor_{record_id}")
                    shipping_charge = st.text_input("Enter Shipping Charge (₹)", key=f"ship_{record_id}")

                    col1, col2 = st.columns(2)
                    approve_order = col1.form_submit_button("✅ Approve & Send Order")
                    request_info = col2.form_submit_button("📦 Request Shipment Info")

                    # APPROVE & SEND ORDER 
                    if approve_order:
                        if not vendor_email_input:
                            st.error("❌ Please enter a vendor email.")
                        else:
                            try:
                                total_price = float(price or 0) + float(shipping_charge or 0)
                            except ValueError:
                                total_price = 0

                            vendor_message = f"""
Dear Vendor,

Please ship the following product to the customer:

- Product Name: {product_name or "N/A"}
- Quantity: {quantity or "N/A"}
- Unit Price: ₹{price or "N/A"}
- Shipping Charge: ₹{shipping_charge or "N/A"}
- Total Price: ₹{total_price}

Kindly attach at least 2 food safety certificates with your shipment confirmation.

Best regards,  
AI Shipping Manager
"""
                            send_vendor_email(
                                vendor_email_input,
                                product_name=product_name or "N/A",
                                price=price or "N/A",
                                quantity=quantity or "N/A",
                                order_id=details.get("order_id"),
                                query_type="order",
                                vendor_message=vendor_message,
                            )
                      
                            mark_as_approved(record_id)
                            st.success(f"✅ Approved and order sent to vendor: {vendor_email_input}")

                    # REQUEST SHIPMENT INFO 
                    if request_info:
                        if not vendor_email_input:
                            st.error("❌ Please enter a vendor email.")
                        else:
                            order_id_match = re.search(r'order\s*id\s*(\d+)', email_text, re.IGNORECASE)
                            order_id = order_id_match.group(1) if order_id_match else details.get("order_id") or "Unknown"

                            enquiry_message = f"""
Dear Vendor,

We have received a shipment enquiry from a customer.

- Order ID: {order_id}
- Customer Email: {sender_email}

Please provide the latest delivery status, estimated dispatch date, and tracking details (if available).
Attach at least 2 food safety certificates with your reply.

Best regards,  
AI Order Enquiry Assistant
"""
                            send_vendor_email(
                                vendor_email_input,
                                product_name=f"Shipment Enquiry - Order {order_id}",
                                price=0,
                                quantity="N/A",
                                order_id=order_id,
                                query_type="shipping",
                                vendor_message=enquiry_message,
                            )
                            st.info(f"📨 Shipment enquiry sent to vendor ({vendor_email_input}) for Order ID {order_id}.")


# SECTION 2: (Manager Review)
st.subheader("📦 Vendor Updates (Pending Manager Review)")

pending_updates = get_pending_vendor_updates()
if not pending_updates:
    st.info("✅ No pending vendor updates for review.")
else:
    for v in pending_updates:
        (
            record_id,
            sender_email,
            email_text,
            reply_text,
            product_name,
            price,
            quantity,
            ready_for_approval,
            approved,
            vendor_status,
            payment_amount,
            manager_decision,
            vendor_pdf1,
            vendor_pdf2,
            vendor_email,
            *rest
        ) = tuple(v) + (None,) * (15 - len(v))

        display_email = vendor_email or sender_email

        with st.expander(f"Vendor Update — Record #{record_id} — From: {display_email}"):
            st.markdown(f"**📦 Shipment Status:** {vendor_status or 'N/A'}")
            st.markdown(f"**💰 Payment Amount:** ₹{payment_amount or 'N/A'}")

            # PDF DOWNLOAD 
            st.markdown("### 📎 Certificates Received")
            col_pdf = st.columns(2)

            if vendor_pdf1 and os.path.exists(vendor_pdf1):
                with col_pdf[0]:
                    with open(vendor_pdf1, "rb") as f:
                        st.download_button("📄 Download Certificate 1", f, file_name=os.path.basename(vendor_pdf1))
            else:
                col_pdf[0].text("Certificate 1: Not available")

            if vendor_pdf2 and os.path.exists(vendor_pdf2):
                with col_pdf[1]:
                    with open(vendor_pdf2, "rb") as f:
                        st.download_button("📄 Download Certificate 2", f, file_name=os.path.basename(vendor_pdf2))
            else:
                col_pdf[1].text("Certificate 2: Not available")

            # MANAGER APPROVAL / REJECTION 
            st.markdown("---")
            col1, col2 = st.columns(2)

            # Approve
            if col1.button(f"✅ Approve (Record {record_id})"):
                update_manager_decision(record_id, "Approved")

                vendor_msg = f"""Dear Vendor,

We have reviewed the submitted food safety certificates for Record {record_id} and they are approved.
Please proceed with shipment and provide tracking details/POD when available.

Best regards,  
AI Shipping Manager
"""
                try:
                    send_email(display_email, f"Certificates Approved — Record {record_id}", vendor_msg)
                    st.success("✅ Vendor notified about approval.")
                except Exception as e:
                    st.error(f"Failed to send approval email to vendor: {e}")

                try:
                    send_customer_update(sender_email, vendor_status, payment_amount, approved=True)
                    st.success("✅ Customer updated about shipment approval.")
                except Exception as e:
                    st.error(f"Failed to notify customer: {e}")

            # Reject
            if col2.button(f"❌ Reject (Record {record_id})"):
                update_manager_decision(record_id, "Rejected")

                vendor_msg = f"""Dear Vendor,

After reviewing the submitted food safety certificates for Record {record_id}, we found them insufficient or invalid.
Please resend valid food safety certificates (at least 2 valid PDFs) and include any missing shipment proof.

Best regards,  
AI Shipping Manager
"""
                try:
                    send_email(display_email, f"Certificates Rejected — Record {record_id}", vendor_msg)
                    st.warning("❌ Vendor notified about rejection.")
                except Exception as e:
                    st.error(f"Failed to send rejection email: {e}")

                try:
                    send_customer_update(sender_email, vendor_status, payment_amount, approved=False)
                    st.warning("❌ Customer informed about delay due to rejection.")
                except Exception as e:
                    st.error(f"Failed to notify customer: {e}")