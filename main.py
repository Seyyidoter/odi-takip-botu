import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# GitHub Secrets verileri
EMAIL_USER = os.environ.get("MY_EMAIL")
EMAIL_PASS = os.environ.get("MY_EMAIL_PASSWORD") 
ODI_EMAIL = os.environ.get("ODI_EMAIL")
ODI_PASSWORD = os.environ.get("ODI_PASSWORD")

# Alıcı Listesi
EXTRA_EMAILS = [
    "denizdevseli@std.iyte.edu.tr",
    "ruyaerdogan@std.iyte.edu.tr"
]

def send_mail(subject, message):
    recipients = [EMAIL_USER] + EXTRA_EMAILS
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipients, msg.as_string())
        print(f"Mail gönderildi (Toplam {len(recipients)} kişi): " + subject)
    except Exception as e:
        print(f"Mail hatasi: {e}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Siteye gidiliyor...")
        page.goto("https://getodi.com/sign-in/") 
        
        # --- LOGIN ---
        try:
            print("Login deneniyor...")
            page.fill('input[name="username"]', ODI_EMAIL) 
            page.fill('input[name="password"]', ODI_PASSWORD)
            page.click('.btn-sign-01')
            page.wait_for_timeout(5000) 
            
        except Exception as e:
            print(f"Login hatasi: {e}")
            send_mail("ODI TEST HATASI", f"Giriş başarısız: {e}")
            browser.close()
            return

        print("Ogrenci sayfasina geciliyor...")
        page.goto("https://getodi.com/student/")
        page.wait_for_timeout(5000)

        content = page.content().lower()

        # --- KONTROL ---
        if "izmir" in content:
            print("İzmir bulundu!")
            send_mail(
                "MÜJDE: İzmir Restoranı Yakalandı!", 
                "GetOdi sayfasında İzmir restoranı tespit edildi. Hemen bak: https://getodi.com/student/"
            )
        else:
            print("İzmir yok ama test için mail atılıyor...")
            # TEST İÇİN BURASI EKLENDİ
            send_mail(
                "Sistem Testi: İzmir Yok", 
                "Bu bir test mailidir. Sistem sorunsuz çalışıyor ve mailleri iletiyor. Şu an İzmir restoranı yok."
            )

        browser.close()

if __name__ == "__main__":
    run()
