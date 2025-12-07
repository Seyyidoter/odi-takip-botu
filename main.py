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

def send_mail(subject, message):
    # Ana alıcı (siz) + Ekstra liste
    recipients = [EMAIL_USER] + EXTRA_EMAILS
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    # Mail başlığında herkesin adresi görünsün diye birleştiriyoruz
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            # sendmail fonksiyonuna tüm listeyi veriyoruz
            server.sendmail(EMAIL_USER, recipients, msg.as_string())
        print(f"Mail başarıyla gönderildi (Toplam {len(recipients)} kişi).")
    except Exception as e:
        print(f"Mail gönderme hatası: {e}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Geniş ve uzun bir ekran açıyoruz
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
            # Login olamazsa haber ver (Sistemin bozulduğunu anlamanız için)
            send_mail("ODI BOT HATASI", f"Giris yapilamadi: {e}")
            browser.close()
            return

        print("Öğrenci sayfasına (Sıralı Liste) geçiliyor...")
        # URL PARAMETRESİ İLE SIRALAMA: ?sort=count (Yemek olanlar en üstte)
        page.goto("https://getodi.com/student/?sort=count")
        page.wait_for_timeout(5000)

        # --- SCROLL (KAYDIRMA) ---
        print("Sayfa taranıyor (Klavye 'End' Tuşu ile)...")
        # 10 kere basıyoruz, listeyi tamamen yüklüyoruz.
        for i in range(10): 
            page.keyboard.press("End")
            time.sleep(1.5) 
        
        page.wait_for_timeout(2000)

        # --- ANALİZ ---
        print("Restoranlar kontrol ediliyor...")
        cards = page.query_selector_all(".menu-box")
        print(f"Toplam {len(cards)} kutu tarandı.")

        toplam_yemek_sayisi = 0
        bulunan_yerler = []

        for card in cards:
            raw_text = card.inner_text()
            text_lower = raw_text.lower()
            
            # 'zmir' araması (Türkçe karakter sorununa karşı önlem)
            if "zmir" in text_lower:
                try:
                    count = 0
                    count_element = card.query_selector(".menu-capacity span")
                    if count_element:
                        count = int(count_element.inner_text().strip())
                        
                    # --- KRİTİK KONTROL ---
                    # Sadece yemek sayısı 1 veya daha fazlaysa işleme al
                    if count >= 1:
                        print(f"--> BINGO! Aktif yemek bulundu: {count} adet")
                        toplam_yemek_sayisi += count
                        
                        # Restoran adını al
                        lines = raw_text.split('\n')
                        restoran_adi = lines[1] if len(lines) > 1 else "Bilinmiyor"
                        
                        bulunan_yerler.append(f"{restoran_adi} ({count} adet)")
                    else:
                        # Loglara yaz ama mail atma
                        # print(f"İzmir restoranı görüldü ama boş: {count}")
                        pass

                except Exception as e:
                    print(f"Okuma hatası: {e}")

        # --- SONUÇ VE MAİL ---
        if toplam_yemek_sayisi >= 1:
            print(f"SONUÇ: Toplam {toplam_yemek_sayisi} yemek bulundu. Mail gönderiliyor.")
            
            detay_mesaji = "\n".join(bulunan_yerler)
            mail_govdesi = f"Müjde! İzmir'de şu an {toplam_yemek_sayisi} adet askıda yemek var.\n\n"
            mail_govdesi += f"Bulunan Yerler:\n{detay_mesaji}\n\n"
            mail_govdesi += "Hemen kapmak için: https://getodi.com/student/"
            
            send_mail(
                f"ALARM: İzmir'de {toplam_yemek_sayisi} Yemek Var!", 
                mail_govdesi
            )
        else:
            print("SONUÇ: İzmir restoranları tarandı, ancak aktif yemek (>=1) bulunamadı. Mail atılmıyor.")

        browser.close()

if __name__ == "__main__":
    run()
