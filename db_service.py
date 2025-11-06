import sqlite3
import os

DB_FILE = "emails.db"

# ---------------------------
# Initialize DB & safe columns
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Main table
    c.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_email TEXT,
        email_text TEXT,
        reply_text TEXT,
        product_name TEXT,
        price TEXT,
        quantity TEXT,
        ready_for_approval BOOLEAN,
        approved BOOLEAN DEFAULT 0,
        vendor_status TEXT DEFAULT NULL,
        payment_amount TEXT DEFAULT NULL,
        manager_decision TEXT DEFAULT NULL
    )
    """)

    # Add PDF columns if missing
    columns = [row[1] for row in c.execute("PRAGMA table_info(emails);")]
    if "vendor_pdf1" not in columns:
        c.execute("ALTER TABLE emails ADD COLUMN vendor_pdf1 TEXT DEFAULT NULL")
    if "vendor_pdf2" not in columns:
        c.execute("ALTER TABLE emails ADD COLUMN vendor_pdf2 TEXT DEFAULT NULL")

    # Add vendor_email column if missing
    if "vendor_email" not in columns:
        c.execute("ALTER TABLE emails ADD COLUMN vendor_email TEXT DEFAULT NULL")

    conn.commit()
    conn.close()


# ---------------------------
# Insert a new email record
# ---------------------------
def insert_record(sender, email_text, reply_text, product_name, price, quantity, ready):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    INSERT INTO emails (
        sender_email, email_text, reply_text, product_name, price, quantity, ready_for_approval
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sender, email_text, reply_text, product_name, price, quantity, ready))
    conn.commit()
    conn.close()


# ---------------------------
# Fetch all records
# ---------------------------
def get_all_records():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM emails ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# ---------------------------
# Mark as approved
# ---------------------------
def mark_as_approved(record_id, vendor_email=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if vendor_email:
        c.execute("UPDATE emails SET approved = 1, vendor_email = ? WHERE id = ?", (vendor_email, record_id))
    else:
        c.execute("UPDATE emails SET approved = 1 WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


# ---------------------------
# Update vendor info by record ID
# ---------------------------
def save_vendor_update(record_id, vendor_status, payment_amount, pdf1_path=None, pdf2_path=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE emails
        SET vendor_status = ?, payment_amount = ?, ready_for_approval = 1,
            vendor_pdf1 = ?, vendor_pdf2 = ?
        WHERE id = ?
    """, (vendor_status, payment_amount, pdf1_path, pdf2_path, record_id))
    conn.commit()
    conn.close()


# ---------------------------
# Update vendor info by sender email (or most recent unmatched record)
# ---------------------------
def update_vendor_reply(sender_email, vendor_status, payment_amount, pdf1_path=None, pdf2_path=None, vendor_email=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT id FROM emails
        WHERE sender_email = ? AND vendor_status IS NULL
        ORDER BY id DESC LIMIT 1
    """, (sender_email,))
    row = c.fetchone()

    if not row:
        c.execute("""
            SELECT id FROM emails
            WHERE vendor_status IS NULL
            ORDER BY id DESC LIMIT 1
        """)
        row = c.fetchone()

    if row:
        record_id = row[0]
        c.execute("""
            UPDATE emails
            SET vendor_status = ?, payment_amount = ?, ready_for_approval = 1,
                vendor_pdf1 = COALESCE(?, vendor_pdf1),
                vendor_pdf2 = COALESCE(?, vendor_pdf2),
                vendor_email = COALESCE(?, vendor_email)
            WHERE id = ?
        """, (vendor_status, payment_amount, pdf1_path, pdf2_path, vendor_email, record_id))

    conn.commit()
    conn.close()



# ---------------------------
# Manager decision
# ---------------------------
def update_manager_decision(record_id, decision):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE emails
        SET manager_decision = ?
        WHERE id = ?
    """, (decision, record_id))
    conn.commit()
    conn.close()


# ---------------------------
# Fetch vendor updates pending manager approval
# Only show if PDFs exist on disk
# ---------------------------
def get_pending_vendor_updates():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT * FROM emails
        WHERE vendor_status IS NOT NULL
          AND manager_decision IS NULL
        ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows



# ---------------------------
# Debug utility
# ---------------------------
def print_all_records():
    rows = get_all_records()
    for r in rows:
        print(r)