import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# GitHub Secrets'tan verileri alacağız
EMAIL_USER = os.environ.get("MY_EMAIL")
EMAIL_PASS = os.environ.get("MY_EMAIL_PASSWORD") 
ODI_EMAIL = os.environ.get("ODI_EMAIL")
ODI_PASSWORD = os.environ.get("ODI_PASSWORD")

# Guncelleme: Konu basligini (subject) disaridan alacak sekilde degistirdik
def send_mail(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
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
        page.goto("https://getodi.com/sign-in/") 
        
        # --- LOGIN ---
        try:
            print("Login formlari dolduruluyor...")
            page.fill('input[name="username"]', ODI_EMAIL) 
            page.fill('input[name="password"]', ODI_PASSWORD)
            
            print("Butona tiklaniyor...")
            page.click('.btn-sign-01')
            
            page.wait_for_timeout(5000) 
            
        except Exception as e:
            print(f"Login hatasi: {e}")
            # Hata alirsa da mail atsin ki bozuldugunu anlayin
            send_mail("ODI HATA", f"Giris yaparken hata olustu: {e}")
            browser.close()
            return

        print("Ogrenci sayfasina geciliyor...")
        page.goto("https://getodi.com/student/")
        page.wait_for_timeout(5000)

        content = page.content().lower()

        # --- KONTROL MEKANIZMASI ---
        if "izmir" in content:
            print("Izmir bulundu!")
            send_mail(
                "MÜJDE: İzmir Restoranı Var!", 
                "GetOdi sayfasında İzmir ile ilgili içerik tespit edildi. Hemen kontrol et: https://getodi.com/student/"
            )
        else:
            print("Izmir henuz yok.")
            # BURASI YENI EKLENDI: Yoksa da mail at
            send_mail(
                "Durum Raporu: İzmir Yok", 
                "Site kontrol edildi, şu an İzmir için aktif bir restoran görünmüyor."
            )

        browser.close()

if __name__ == "__main__":
    run()
