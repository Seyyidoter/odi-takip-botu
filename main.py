import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# GitHub Secrets verileri
EMAIL_USER = os.environ.get("MY_EMAIL")
EMAIL_PASS = os.environ.get("MY_EMAIL_PASSWORD") 
ODI_EMAIL = os.environ.get("ODI_EMAIL")
ODI_PASSWORD = os.environ.get("ODI_PASSWORD")

def send_mail(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
        print("Mail gönderildi: " + subject)
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
            send_mail("ODI BOT HATASI", f"Giris yapilamadi. Hata: {e}")
            browser.close()
            return

        print("Ogrenci sayfasina geciliyor...")
        page.goto("https://getodi.com/student/")
        page.wait_for_timeout(5000)

        content = page.content().lower()

        # --- KONTROL (İZMİR) ---
        if "izmir" in content:
            print("İzmir bulundu!")
            send_mail(
                "MÜJDE: İzmir Restoranı Yakalandı!", 
                "GetOdi sayfasında İzmir restoranı tespit edildi. Hemen bak: https://getodi.com/student/"
            )
        else:
            print("İzmir henüz yok.")
            # Eğer saat başı "yok" maili gelmesinden sıkılırsanız
            # aşağıdaki send_mail satırının başına # koyarak kapatabilirsiniz.
            send_mail(
                "Durum Raporu: İzmir Yok", 
                "Site kontrol edildi, şu an İzmir görünmüyor."
            )

        browser.close()

if __name__ == "__main__":
    run()
