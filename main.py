import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# GitHub Secrets'tan verileri alacağız
EMAIL_USER = os.environ.get("MY_EMAIL")
EMAIL_PASS = os.environ.get("MY_EMAIL_PASSWORD") 
ODI_EMAIL = os.environ.get("ODI_EMAIL")
ODI_PASSWORD = os.environ.get("ODI_PASSWORD")

def send_mail(message):
    msg = MIMEText(message)
    msg['Subject'] = 'ODI ALARM: Izmir Restorani Bulundu!'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
        print("Mail gonderildi.")
    except Exception as e:
        print(f"Mail hatasi: {e}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Siteye gidiliyor...")
        page.goto("https://getodi.com/login") 
        
        # --- LOGIN ---
        # Not: Bu kisimlar sitenin guncel yapisina gore degisebilir.
        # Telefondan F12 yapamayacagimiz icin standart isimleri deniyoruz.
        try:
            page.fill('input[name="email"]', ODI_EMAIL) 
            page.fill('input[name="password"]', ODI_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000) 
        except Exception as e:
            print(f"Login hatasi (selector yanlis olabilir): {e}")

        print("Ogrenci sayfasina geciliyor...")
        page.goto("https://getodi.com/student/")
        page.wait_for_timeout(5000)

        content = page.content().lower()

        # Izmir kontrolu
        if "izmir" in content:
            print("Izmir bulundu!")
            send_mail("Mujde! GetOdi sayfasinda Izmir ile ilgili icerik tespit edildi: https://getodi.com/student/")
        else:
            print("Izmir henuz yok.")

        browser.close()

if __name__ == "__main__":
    run()
