import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

TARGET_URL = os.environ["TARGET_URL"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]
KEYWORD = "加古川"  # 監視するキーワード
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

def main():
    content = get_page_content()

    # 加古川のチケットに関する部分だけ抽出
    if KEYWORD not in content:
        print(f"「{KEYWORD}」の情報がページに見つかりません")
        return

    current_hash = get_hash(content)

    if not os.path.exists(PREVIOUS_HASH_FILE):
        with open(PREVIOUS_HASH_FILE, "w") as f:
            f.write(current_hash)
        print("初回実行：ハッシュを保存しました")
        return

    with open(PREVIOUS_HASH_FILE, "r") as f:
        previous_hash = f.read().strip()

    if current_hash != previous_hash:
        with open(PREVIOUS_HASH_FILE, "w") as f:
            f.write(current_hash)
        send_email(
            "【速報】レミオロメン加古川のチケット情報が更新されました！",
            f"リセールチケットが出た可能性があります！今すぐ確認してください。\n\n{TARGET_URL}"
        )
        print("変化を検知！メールを送信しました。")
    else:
        print("変化なし")

if __name__ == "__main__":
    main()
