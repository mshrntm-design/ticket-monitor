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

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]

TARGETS = [

    {
        "name": "矢井田瞳7/4クラブ月世界【ローチケ】",
        "url": os.environ["TARGET_URL_YAHIDA_LTIKE"],
        "css": ".AccordionBox__itemStatus",
        "hash_file": "hash_yahida_ltike.txt",
        "perf_cd": None,
    },
    {
        "name": "矢井田瞳7/4クラブ月世界【eプラス】",
        "url": os.environ["TARGET_URL_YAHIDA_EPLUS"],
        "css": ".ticket-status__item",
        "hash_file": "hash_yahida_eplus.txt",
        "perf_cd": None,
    },
    {
        "name": "CHEMISTRY三田9/12【チケットぴあ】",
        "url": os.environ["TARGET_URL_CHEMISTRY_PIA"],
        "css": ".ticketSelect__icon",
        "hash_file": "hash_chemistry_pia.txt",
        "perf_cd": "001",
    },
    {
        "name": "CHEMISTRY三田9/12【ローチケ】",
        "url": os.environ["TARGET_URL_CHEMISTRY_LTIKE"],
        "css": ".AccordionBox__itemStatus",
        "hash_file": "hash_chemistry_ltike.txt",
        "perf_cd": None,
    },
    {
        "name": "CHEMISTRY三田9/12【eプラス】",
        "url": os.environ["TARGET_URL_CHEMISTRY_EPLUS"],
        "css": ".ticket-status__item",
        "hash_file": "hash_chemistry_eplus.txt",
        "perf_cd": None,
    },
]

def get_status(url, css, perf_cd=None):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )
    except Exception:
        pass
    time.sleep(3)

    if perf_cd:
        try:
            section = driver.find_element(By.CSS_SELECTOR, f"[data-perf-cd='{perf_cd}']")
            elements = section.find_elements(By.CSS_SELECTOR, css)
        except Exception:
            elements = driver.find_elements(By.CSS_SELECTOR, css)
    else:
        elements = driver.find_elements(By.CSS_SELECTOR, css)

    status_text = "\n".join([el.text.replace("warning\n", "").strip() for el in elements if el.text.strip()])
    driver.quit()
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

def save_hash_to_repo(hash_file, hash_value):
    with open(hash_file, "w") as f:
        f.write(hash_value)
    subprocess.run(["git", "config", "user.email", "monitor@github.com"])
    subprocess.run(["git", "config", "user.name", "Monitor Bot"])
    subprocess.run(["git", "add", hash_file])
    result = subprocess.run(["git", "commit", "-m", f"Update {hash_file}"], capture_output=True)
    if result.returncode == 0:
        subprocess.run(["git", "push"])

def check_target(target):
    print(f"\n--- {target['name']} ---")
    status_text = get_status(target["url"], target["css"], target.get("perf_cd"))

    if not status_text.strip():
        print("状況が取得できませんでした")
        return

    print(f"現在の状況：{status_text}")
    current_hash = get_hash(status_text)

    if not os.path.exists(target["hash_file"]):
        save_hash_to_repo(target["hash_file"], current_hash)
        print("初回実行：状態を保存しました")
        return

    with open(target["hash_file"], "r") as f:
        previous_hash = f.read().strip()

    if current_hash != previous_hash:
        save_hash_to_repo(target["hash_file"], current_hash)
        send_email(
            f"【速報】{target['name']}のチケット状況が変化しました！",
            f"チケットの状況が変わりました！今すぐ確認してください。\n\n現在の状況：\n{status_text}\n\n{target['url']}"
        )
        print("変化を検知！メールを送信しました。")
    else:
        print("変化なし")

def main():
    for target in TARGETS:
        check_target(target)

if __name__ == "__main__":
    main()
