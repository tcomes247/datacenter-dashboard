
from apscheduler.schedulers.blocking import BlockingScheduler
from email import message_from_bytes
from imaplib import IMAP4_SSL
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER")

def fetch_emails():
    with IMAP4_SSL(IMAP_SERVER) as mail:
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, 'UNSEEN')
        for num in messages[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            msg = message_from_bytes(data[0][1])
            print("Fetched email from:", msg["From"])

scheduler = BlockingScheduler()
scheduler.add_job(fetch_emails, 'interval', minutes=10)

if __name__ == "__main__":
    scheduler.start()
