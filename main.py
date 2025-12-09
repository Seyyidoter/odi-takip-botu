import os
import smtplib
import time
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# GitHub Secrets verileri
EMAIL_USER = os.environ.get("MY_EMAIL")
EMAIL_PASS = os.environ.get("MY_EMAIL_PASSWORD") 
ODI_EMAIL = os.environ.get("ODI_EMAIL")
ODI_PASSWORD = os.environ.get("ODI_PASSWORD")

# Alıcı Listesi (Siz + Arkadaşlarınız)
EXTRA_EMAILS = [
    "denizdevseli@std.iyte.edu.tr",
    "ruyaerdogan@std.iyte.edu.tr"
]

def send_mail(subject, message_html):
    # Ana alıcı (siz) + Ekstra liste
    recipients = [EMAIL_USER] + EXTRA_EMAILS
    
    # --- DEĞİŞİKLİK BURADA ---
    # İkinci parametre olarak 'html' ekledik. Artık HTML kodlarını anlar.
    msg = MIMEText(message_html, 'html')
    
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipients, msg.as_string())
        print(f"Mail başarıyla gönderildi (Toplam {len(recipients)} kişi).")
    except Exception as e:
        print(f"Mail gönderme hatası: {e}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 2000})

        print("Siteye gidiliyor...")
        page.goto("https://getodi.com/sign-in/") 
        
        # --- LOGIN ---
        try:
            print("Login yapılıyor...")
            page.fill('input[name="username"]', ODI_EMAIL) 
            page.fill('input[name="password"]', ODI_PASSWORD)
            page.click('.btn-sign-01')
            page.wait_for_timeout(5000) 
        except Exception as e:
            print(f"Login hatasi: {e}")
            send_mail("ODI BOT HATASI", f"Giris yapilamadi: {e}")
            browser.close()
            return

        print("Öğrenci sayfasına (Sıralı Liste) geçiliyor...")
        page.goto("https://getodi.com/student/?sort=count")
        page.wait_for_timeout(5000)

        # --- SCROLL (KAYDIRMA) ---
        print("Sayfa taranıyor (Klavye 'End' Tuşu ile)...")
        for i in range(10): 
            page.keyboard.press("End")
            time.sleep(1.5) 
        
        page.wait_for_timeout(2000)

        # --- ANALİZ ---
        print("Restoranlar kontrol ediliyor...")
        cards = page.query_selector_all(".menu-box")
        print(f"Toplam {len(cards)} kutu tarandı.")

        toplam_yemek_sayisi = 0
        bulunan_yerler_html = "" # Restoranları HTML listesi olarak biriktireceğiz

        for card in cards:
            raw_text = card.inner_text()
            text_lower = raw_text.lower()
            
            if "zmir" in text_lower:
                try:
                    count = 0
                    count_element = card.query_selector(".menu-capacity span")
                    if count_element:
                        count = int(count_element.inner_text().strip())
                        
                    if count >= 1:
                        print(f"--> BINGO! Aktif yemek bulundu: {count} adet")
                        toplam_yemek_sayisi += count
                        
                        lines = raw_text.split('\n')
                        restoran_adi = lines[1] if len(lines) > 1 else "Bilinmiyor"
                        
                        # HTML Liste maddesi ekliyoruz (<li>)
                        bulunan_yerler_html += f"<li><b>{restoran_adi}</b>: {count} adet</li>"
                    else:
                        pass

                except Exception as e:
                    print(f"Okuma hatası: {e}")

        # --- SONUÇ VE MAİL ---
        if toplam_yemek_sayisi >= 1:
            print(f"SONUÇ: Toplam {toplam_yemek_sayisi} yemek bulundu. Mail gönderiliyor.")
            
            # --- HTML MAİL FORMATI ---
            mail_govdesi = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2e7d32;">İzmir'de {toplam_yemek_sayisi} adet yemek var.</h2>
                <p><b>Bulunan Restoranlar:</b></p>
                <ul>
                  {bulunan_yerler_html}
                </ul>
                <br>
                <p style="font-size: 16px;">
                    Hemen kapmak için aşağıdaki linke tıkla:<br>
                    <a href="https://getodi.com/student/" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;">
                        👉 Odi'ye Git (Tıkla)
                    </a>
                </p>
                <p style="font-size: 12px; color: grey;">Bu mail otomatik gönderilmiştir.</p>
              </body>
            </html>
            """
            
            send_mail(
                f"ALARM: İzmir'de {toplam_yemek_sayisi} Yemek Var!", 
                mail_govdesi
            )
        else:
            print("SONUÇ: İzmir restoranları tarandı, ancak aktif yemek (>=1) bulunamadı. Mail atılmıyor.")

        browser.close()

if __name__ == "__main__":
    run()
