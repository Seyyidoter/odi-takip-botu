import os
import smtplib
import time
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# GitHub Secrets
EMAIL_USER = os.environ.get("MY_EMAIL")
EMAIL_PASS = os.environ.get("MY_EMAIL_PASSWORD") 
ODI_EMAIL = os.environ.get("ODI_EMAIL")
ODI_PASSWORD = os.environ.get("ODI_PASSWORD")

def send_mail(subject, message):
    recipients = [EMAIL_USER] # Sadece size test maili
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipients, msg.as_string())
        print(f"Mail gönderildi: {subject}")
    except Exception as e:
        print(f"Mail hatasi: {e}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Ekranı çok uzun yapalım
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
            browser.close()
            return

        print("Öğrenci sayfasına (Sıralı Liste) geçiliyor...")
        # DÜZELTME 1: Sıralamayı URL'den zorluyoruz (?sort=count)
        # Böylece yemek varsa en üstte çıkar.
        page.goto("https://getodi.com/student/?sort=count")
        page.wait_for_timeout(5000)

        # --- SCROLL ---
        print("Sayfa taranıyor (Klavye 'End' Tuşu ile)...")
        # 10 kere basıyoruz, 80-100 restoran garanti gelir.
        for i in range(10): 
            page.keyboard.press("End")
            time.sleep(1.5) 
        
        page.wait_for_timeout(2000)

        # --- TARAMA ---
        cards = page.query_selector_all(".menu-box")
        print(f"Toplam {len(cards)} kutu tarandı.")

        bulunan_izmir_restoranlari = []
        
        # Debug için ilk 3 restoranın adını yazdıralım (Doğru okuyor mu?)
        print("Örnek okunan ilk 3 restoran:")
        for i, card in enumerate(cards[:3]):
            print(f" - {card.inner_text().splitlines()[1]}")

        for card in cards:
            raw_text = card.inner_text()
            # DÜZELTME 2: 'İ' harfi sorununu aşmak için 'zmir' arıyoruz.
            # Ve tüm metni küçük harfe çeviriyoruz.
            text_lower = raw_text.lower()
            
            # Hem 'izmir' hem 'zmir' kontrolü (Garanti olsun)
            if "zmir" in text_lower:
                try:
                    count = 0
                    count_element = card.query_selector(".menu-capacity span")
                    if count_element:
                        count = int(count_element.inner_text().strip())
                    
                    # İsim temizleme
                    lines = raw_text.split('\n')
                    # Genelde 2. satır restoran adıdır
                    ozet_isim = lines[1] if len(lines) > 1 else "İsimsiz"
                    
                    durum = f"RESTORAN: {ozet_isim} | ADET: {count}"
                    print(f"BULUNDU -> {durum}")
                    bulunan_izmir_restoranlari.append(durum)
                    
                except Exception as e:
                    print(f"Okuma hatası: {e}")

        # --- RAPOR ---
        mail_icerigi = f"Bot Raporu (Sıralama: Çok->Az):\n\n"
        mail_icerigi += f"Toplam Taranan Kutu: {len(cards)}\n"
        
        if bulunan_izmir_restoranlari:
            mail_icerigi += f"Bulunan İzmir Restoranları ({len(bulunan_izmir_restoranlari)} adet):\n" 
            mail_icerigi += "\n".join(bulunan_izmir_restoranlari)
        else:
            mail_icerigi += "Listede hiç İzmir (zmir) kelimesi geçmedi."

        send_mail(f"TEST: {len(bulunan_izmir_restoranlari)} İzmir Bulundu", mail_icerigi)

        browser.close()

if __name__ == "__main__":
    run()
