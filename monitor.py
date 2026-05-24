import os
import hashlib
import smtplib
import subprocess
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

TARGET_URL = os.environ["TARGET_URL"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]
PREVIOUS_HASH_FILE = "previous_hash.txt"

def get_page_content():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.get(TARGET_URL)
    time.sleep(5)
    content = driver.page_source
    driver.quit()
    return content

def get_hash(content):
    return hashlib.md5(content.encode()).hexdigest()

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        smtp.send_message(msg)

def save_hash_to_repo(hash_value):
    with open(PREVIOUS_HASH_FILE, "w") as f:
        f.write(hash_value)
    subprocess.run(["git", "config", "user.email", "monitor@github.com"])
    subprocess.run(["git", "config", "user.name", "Monitor Bot"])
    subprocess.run(["git", "add", PREVIOUS_HASH_FILE])
    subprocess.run(["git", "commit", "-m", "Update hash"])
    subprocess.run(["git", "push"])

def main():
    content = get_page_content()
    current_hash = get_hash(content)

    if not os.path.exists(PREVIOUS_HASH_FILE):
        save_hash_to_repo(current_hash)
        print("初回実行：ハッシュを保存しました")
        return

    with open(PREVIOUS_HASH_FILE, "r") as f:
        previous_hash = f.read().strip()

    if current_hash != previous_hash:
        save_hash_to_repo(current_hash)
        send_email(
            "【速報】レミオロメン加古川のチケット情報が更新されました！",
            f"リセールチケットが出た可能性があります！今すぐ確認してください。\n\n{TARGET_URL}"
        )
        print("変化を検知！メールを送信しました。")
    else:
        print("変化なし")

if __name__ == "__main__":
    main()
