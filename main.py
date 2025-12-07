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

# SADECE SİZE MAİL ATAN TEST VERSİYONU
def send_mail(subject, message):
    recipients = [EMAIL_USER]
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
        # Ekranı dikey olarak da uzun tutalım
        page = browser.new_page(viewport={'width': 1366, 'height': 1200})

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
            send_mail("ODI TEST HATASI", f"Giris yapilamadi: {e}")
            browser.close()
            return

        print("Öğrenci sayfasına geçiliyor...")
        page.goto("https://getodi.com/student/")
        # Sayfanın ilk yüklenmesi için iyi bir süre bekleyelim
        page.wait_for_timeout(5000)

        # --- GÜÇLÜ SCROLL (KAYDIRMA) ---
        print("Sayfa sonuna kadar kaydırılıyor (Klavye 'End' Tuşu ile)...")
        
        # 10 kere 'End' tuşuna basıp bekleyeceğiz. Bu, fare tekerleğinden daha etkilidir.
        for i in range(10): 
            print(f"Kaydırma {i+1}/10...")
            page.keyboard.press("End")
            time.sleep(2) # Yüklenmesi için 2 saniye bekle
        
        # Son bir kez daha bekle
        page.wait_for_timeout(3000)

        # --- TARAMA VE SAYIM ---
        print("Restoranlar analiz ediliyor...")
        cards = page.query_selector_all(".menu-box")
        toplam_kutu_sayisi = len(cards)
        print(f"Toplam {toplam_kutu_sayisi} adet restoran kutusu bulundu.")

        bulunan_izmir_restoranlari = []

        for card in cards:
            raw_text = card.inner_text()
            text_lower = raw_text.lower()
            
            # İzmir kontrolü
            if "izmir" in text_lower:
                try:
                    count = 0
                    count_element = card.query_selector(".menu-capacity span")
                    if count_element:
                        count = int(count_element.inner_text().strip())
                    
                    # Restoran ismini temizleyip alalım
                    lines = raw_text.split('\n')
                    ozet_isim = lines[1] if len(lines) > 1 else "İsimsiz"
                    
                    # Bilgiyi kaydet
                    durum = f"--> {ozet_isim} (Yemek: {count})"
                    print(durum)
                    bulunan_izmir_restoranlari.append(durum)
                    
                except Exception as e:
                    print(f"Okuma hatası: {e}")

        # --- RAPOR MAİLİ ---
        print("Rapor hazırlanıyor...")
        
        # Mail içeriği
        mail_icerigi = f"Bot Çalışma Raporu:\n\n"
        mail_icerigi += f"Toplam Taranan Restoran Sayısı: {toplam_kutu_sayisi}\n"
        mail_icerigi += f"Bulunan İzmir Restoranı Sayısı: {len(bulunan_izmir_restoranlari)}\n\n"
        
        if bulunan_izmir_restoranlari:
            mail_icerigi += "İzmir Restoran Listesi:\n" + "\n".join(bulunan_izmir_restoranlari)
        else:
            mail_icerigi += "Listede hiç İzmir restoranı bulunamadı."
            
        mail_icerigi += "\n\n(Not: Eğer toplam sayı 10-15 civarıysa scroll çalışmamış demektir. 50+ ise çalışmıştır.)"

        send_mail(f"TEST: {len(bulunan_izmir_restoranlari)} İzmir Bulundu", mail_icerigi)

        browser.close()

if __name__ == "__main__":
    run()
