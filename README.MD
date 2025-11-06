# ai-email-agent

# 📧 AI Email Agent (LangChain + Gmail + Streamlit)

An *AI-powered Email Automation System* that reads Gmail inbox, detects new orders or shipping queries from customers, sends smart replies using *Google Gemini*, and updates vendors + customers automatically.  
Built using *Python, **LangChain, **Streamlit, and **Gmail API*.

---

## 🚀 Features

✅ Automatically reads customer emails from Gmail  
✅ Classifies emails as *New Orders* or *Shipping Queries*  
✅ Sends polite, AI-generated replies using *Gemini 2.5 Flash*  
✅ Notifies vendors and requests shipment certificates  
✅ Reads vendor replies & verifies attached certificates  
✅ Allows manager approval/rejection through *Streamlit dashboard*  
✅ Stores all communication logs in *SQLite database*

---

## 🏗 Tech Stack

- *Python 3.10+*
- *LangChain + Gemini API*
- *Streamlit* (for dashboard)
- *SQLite3* (for database)
- *Google Gmail API*

---

## ⚙ Setup Instructions

### 1️⃣ Clone this repo
bash
git clone https://github.com/yourusername/ai-email-agent.git
cd ai-email-agent

###2️⃣ Create virtual environment

python -m venv myenv
myenv\Scripts\activate   # (Windows)
# or
source myenv/bin/activate  # (Mac/Linux)

###3️⃣ Install dependencies

pip install -r requirements.txt

###4️⃣ Set up .env file
Create a .env file and add your Google Gemini API key:

GOOGLE_API_KEY=your_api_key_here

###5️⃣ Gmail API Setup

1. Go to Google Cloud Console

2. Enable Gmail API

3. Download your OAuth credentials as credentials.json

4. Run your script once to authenticate → It will generate token.json

###▶ Run the App for processing customer mail

python main.py 

For manager dashboard (Streamlit)

streamlit run app.py

###▶ Run the App for processing vendor mail

vendor_reply_service.py

###🧠 Folder Structure

ai-email-agent/
│
├── app.py                    # Streamlit dashboard for manager
├── main.py                   # Main script that processes emails
├── ai_agent.py               # AI logic using Gemini (LangChain)
├── gmail_service.py          # Gmail API read/send logic
├── db_service.py             # SQLite database logic
├── vendor_service.py         # Handles vendor-side email generation
├── vendor_reply_service.py   # Processes vendor reply emails
│
├── requirements.txt          # All dependencies
├── .env                      # API keys (not uploaded)
├── token.json                # Gmail auth token (auto-generated)
└── README.md