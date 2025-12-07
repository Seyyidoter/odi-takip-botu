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

# BU TEST SURUMUDUR: Sadece size mail atar.
def send_mail(subject, message):
    # Sadece kendi mailiniz
    recipients = [EMAIL_USER]
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER # Sadece size

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipients, msg.as_string())
        print(f"Test maili gönderildi: {subject}")
    except Exception as e:
        print(f"Mail hatasi: {e}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Geniş ekran açıyoruz
        page = browser.new_page(viewport={'width': 1280, 'height': 1080})

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
            send_mail("ODI TEST HATASI", f"Giriş başarısız: {e}")
            browser.close()
            return

        print("Öğrenci sayfasına geçiliyor...")
        page.goto("https://getodi.com/student/")
        page.wait_for_timeout(3000)

        # --- SCROLL ---
        print("Sayfa aşağı kaydırılıyor...")
        for i in range(5): 
            page.mouse.wheel(0, 1000) 
            time.sleep(1) 
        
        page.wait_for_timeout(3000)

        # --- TARAMA ---
        print("Restoranlar analiz ediliyor...")
        cards = page.query_selector_all(".menu-box")
        print(f"Toplam {len(cards)} kutu bulundu.")

        bulunan_izmir_restoranlari = []

        for card in cards:
            # Tüm metni alıp küçük harfe çevir
            raw_text = card.inner_text()
            text_lower = raw_text.lower()
            
            if "izmir" in text_lower:
                try:
                    # Sayıyı bul
                    count = 0
                    count_element = card.query_selector(".menu-capacity span")
                    if count_element:
                        count = int(count_element.inner_text().strip())
                    
                    # Restoran ismini bulmaya çalış (Genelde satırlardan biri isimdir)
                    # Basitlik olsun diye ham metnin ilk 2-3 satırını alalım veya temizleyelim
                    lines = raw_text.split('\n')
                    # Genelde 2. veya 3. satır restoran adıdır ama karışık olabilir.
                    # Direkt tüm metni temizleyip özetleyelim:
                    ozet_isim = lines[1] if len(lines) > 1 else "Bilinmeyen Restoran"
                    
                    # Listeye ekle (Sayı 0 olsa bile ekliyoruz!)
                    durum = f"RESTORAN: {ozet_isim} | ADET: {count}"
                    print(f"Bulundu -> {durum}")
                    bulunan_izmir_restoranlari.append(durum)
                    
                except Exception as e:
                    print(f"Hata: {e}")

        # --- RAPORLAMA ---
        if bulunan_izmir_restoranlari:
            print("İzmir restoranları bulundu, rapor maili atılıyor...")
            mesaj_icerigi = "Botun gördüğü İzmir restoranları şunlar:\n\n" + "\n".join(bulunan_izmir_restoranlari)
            
            send_mail(
                "TEST SONUCU: İzmir Listesi", 
                mesaj_icerigi + "\n\nBu mail sadece test amaçlıdır ve sayı 0 olsa bile gönderilmiştir."
            )
        else:
            print("Sayfa tarandı ama 'İzmir' kelimesi geçen hiçbir şey bulunamadı.")
            send_mail("TEST SONUCU: Boş", "Sayfa tarandı ama İzmir restoranı hiç bulunamadı (Scroll sorunu olabilir).")

        browser.close()

if __name__ == "__main__":
    run()
