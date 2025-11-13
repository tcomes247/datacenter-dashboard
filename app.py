from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import imaplib
import email
import time
from threading import Thread
from dotenv import load_dotenv

# ===== Load environment variables =====
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT"))
NUM_PROVIDERS = 15
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 120))

# ===== FastAPI app =====
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Serve templates and static files =====
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ===== Database helper =====
def init_db():
    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            provider TEXT PRIMARY KEY,
            status TEXT,
            subject TEXT
        )
    """)
    for i in range(1, NUM_PROVIDERS + 1):
        provider_name = os.getenv(f"PROVIDER_{i}_NAME")
        if provider_name:
            cursor.execute("""
                INSERT OR IGNORE INTO incidents (provider, status, subject)
                VALUES (?, ?, ?)
            """, (provider_name, "Unknown", ""))
    conn.commit()
    conn.close()

init_db()

# ===== Email fetching and database update =====
def fetch_latest_email(mail, provider_name, provider_email):
    try:
        mail.select("inbox")
        status, data = mail.search(None, f'(FROM "{provider_email}")')
        email_ids = data[0].split()
        if not email_ids:
            update_db(provider_name, "Up", "No incidents")
            return
        latest_email_id = email_ids[-1]
        status, data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        update_db(provider_name, "Down", msg["Subject"])
    except Exception as e:
        update_db(provider_name, "Error", str(e))

def update_db(provider_name, status, subject):
    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidents (provider, status, subject)
        VALUES (?, ?, ?)
        ON CONFLICT(provider) DO UPDATE SET
            status=excluded.status,
            subject=excluded.subject
    """, (provider_name, status, subject))
    conn.commit()
    conn.close()

def update_network_status():
    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            for i in range(1, NUM_PROVIDERS + 1):
                provider_name = os.getenv(f"PROVIDER_{i}_NAME")
                provider_email = os.getenv(f"PROVIDER_{i}_EMAIL")
                if provider_name and provider_email:
                    fetch_latest_email(mail, provider_name, provider_email)
            mail.logout()
        except Exception as e:
            print("IMAP connection error:", e)
        time.sleep(REFRESH_INTERVAL)

Thread(target=update_network_status, daemon=True).start()

# ===== API endpoint =====
@app.get("/status")
def get_status():
    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents")
    data = cursor.fetchall()
    conn.close()
    return {"incidents": data}

# ===== Config endpoint =====
@app.get("/config")
def get_config():
    return {"refresh_interval": REFRESH_INTERVAL}


# ===== Web dashboard =====
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
