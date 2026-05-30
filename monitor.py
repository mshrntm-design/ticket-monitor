import os
import hashlib
import smtplib
import subprocess
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

TARGET_URL = os.environ["TARGET_URL"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]
PREVIOUS_HASH_FILE = "previous_hash.txt"

def get_status_content():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.get(TARGET_URL)

    # 最大15秒待って要素が出るまで待機
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".lt-ticket-list-item__status"))
        )
    except Exception:
        pass

    time.sleep(3)

    # ページ全体のテキストから「予定枚数終了」などを含む部分を取得
    page_source = driver.page_source
    elements = driver.find_elements(By.CSS_SELECTOR, ".lt-ticket-list-item__status")
    status_text = "\n".join([el.text.replace("warning\n", "") for el in elements])

    # 取得できなかった場合はページソースで確認
    if not status_text.strip():
        if "lt-ticket-list-item__status" in page_source:
            status_text = "要素は存在しますがテキスト取得失敗"
        else:
            status_text = ""

    driver.quit()
    print(f"現在のチケット状況：{status_text}")
    return status_text

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
    status_text = get_status_content()

    if not status_text.strip():
        print("チケット状況が取得できませんでした")
        return

    current_hash = get_hash(status_text)

    if not os.path.exists(PREVIOUS_HASH_FILE):
        save_hash_to_repo(current_hash)
        print("初回実行：状態を保存しました")
        return

    with open(PREVIOUS_HASH_FILE, "r") as f:
        previous_hash = f.read().strip()

    if current_hash != previous_hash:
        save_hash_to_repo(current_hash)
        send_email(
            "【速報】レミオロメン加古川のチケット状況が変化しました！",
            f"チケットの状況が変わりました！今すぐ確認してください。\n\n現在の状況：\n{status_text}\n\n{TARGET_URL}"
        )
        print("変化を検知！メールを送信しました。")
    else:
        print("変化なし")

if __name__ == "__main__":
    main()
