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
import requests
import re

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]

TARGETS = [
    {
        "name": "絢香姫路11/22【チケットぴあ公式リセール】",
        "url": os.environ["TARGET_URL_AYAKA_PIA_RESALE"],
        "css": ".sl_validTicket_map",
        "hash_file": "h1.txt",
        "perf_cd": None,
        "keywords": ["姫路", "アクリエ"],
        "use_requests": True,
    },
    {
        "name": "絢香姫路11/22【ローチケ】",
        "url": os.environ["TARGET_URL_AYAKA_LTIKE"],
        "css": ".AccordionBox__itemStatus",
        "hash_file": "h2.txt",
        "perf_cd": None,
        "keywords": [],
        "use_requests": False,
    },
    {
        "name": "絢香姫路11/22【eプラス】",
        "url": os.environ["TARGET_URL_AYAKA_EPLUS"],
        "css": ".ticket-status__item",
        "hash_file": "h3.txt",
        "perf_cd": None,
        "keywords": [],
        "use_requests": False,
    },
]

def fetch_requests(url, css_pattern):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Connection": "keep-alive",
    }
    response = requests.get(url, headers=headers, timeout=30)
    html = response.text
    matches = re.findall(r'class="sl_validTicket_map">([^<]+)<', html)
    return "\n".join(matches)

def fetch_selenium(url, css, perf_cd=None):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=opts)
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
            items = section.find_elements(By.CSS_SELECTOR, css)
        except Exception:
            items = driver.find_elements(By.CSS_SELECTOR, css)
    else:
        items = driver.find_elements(By.CSS_SELECTOR, css)
    result = "\n".join([e.text.replace("warning\n", "").strip() for e in items if e.text.strip()])
    driver.quit()
    return result

def get_hash(content):
    return hashlib.md5(content.encode()).hexdigest()

def notify(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        s.send_message(msg)

def save(hash_file, hash_value):
    with open(hash_file, "w") as f:
        f.write(hash_value)
    subprocess.run(["git", "config", "user.email", "a@b.com"])
    subprocess.run(["git", "config", "user.name", "bot"])
    subprocess.run(["git", "add", hash_file])
    r = subprocess.run(["git", "commit", "-m", "u"], capture_output=True)
    if r.returncode == 0:
        subprocess.run(["git", "push"])

def check(t):
    print(f"\n--- {t['name']} ---")
    if t.get("use_requests"):
        text = fetch_requests(t["url"], t["css"])
    else:
        text = fetch_selenium(t["url"], t["css"], t.get("perf_cd"))

    keywords = t.get("keywords", [])
    if keywords:
        found = [kw for kw in keywords if kw in text]
        if found:
            notify(
                f"【速報】{t['name']}にリセール情報が出ました！",
                f"以下のキーワードが検出されました：{', '.join(found)}\n\n今すぐ確認してください。\n\n{t['url']}"
            )
            print(f"キーワード検出！{found} メールを送信しました。")
        else:
            print(f"キーワードなし：{keywords}")
        return

    if not text.strip():
        print("状況が取得できませんでした")
        return

    print(f"現在の状況：{text}")
    h = get_hash(text)
    if not os.path.exists(t["hash_file"]):
        save(t["hash_file"], h)
        print("初回実行：状態を保存しました")
        return

    with open(t["hash_file"], "r") as f:
        prev = f.read().strip()

    if h != prev:
        save(t["hash_file"], h)
        notify(
            f"【速報】{t['name']}のチケット状況が変化しました！",
            f"チケットの状況が変わりました！今すぐ確認してください。\n\n現在の状況：\n{text}\n\n{t['url']}"
        )
        print("変化を検知！メールを送信しました。")
    else:
        print("変化なし")

def main():
    for t in TARGETS:
        check(t)

if __name__ == "__main__":
    main()
