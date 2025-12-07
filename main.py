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
        print(f"Mail gönderildi: {subject}")
    except Exception as e:
        print(f"Mail hatasi: {e}")

def run():
    with sync_playwright() as p:
        # Browser'ı başlat
        browser = p.chromium.launch(headless=True)
        # Ekranı geniş tut ki daha çok restoran sığsın
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
            # Login olamazsa haber ver
            send_mail("ODI BOT HATASI", f"Giris yapilamadi: {e}")
            browser.close()
            return

        print("Öğrenci sayfasına geçiliyor...")
        page.goto("https://getodi.com/student/")
        page.wait_for_timeout(3000)

        # --- SCROLL (KAYDIRMA) İŞLEMİ ---
        print("Sayfa aşağı kaydırılıyor (Tüm restoranlar yüklensin)...")
        # 5 kere aşağı kaydırıp yüklenmesini bekliyoruz
        for i in range(5): 
            page.mouse.wheel(0, 1000) 
            time.sleep(1) 
        
        page.wait_for_timeout(3000)

        # --- KONTROL ---
        print("Restoran listesi taranıyor...")
        
        cards = page.query_selector_all(".menu-box")
        print(f"Toplam {len(cards)} adet restoran kutusu bulundu.")

        toplam_yemek_sayisi = 0
        bulunan_restoranlar = []

        for card in cards:
            text = card.inner_text().lower()
            
            # 1. Kural: Restoran İZMİR'de mi?
            if "izmir" in text:
                try:
                    # 2. Kural: Yemek sayısını bul
                    count_element = card.query_selector(".menu-capacity span")
                    if count_element:
                        count_text = count_element.inner_text().strip()
                        count = int(count_text)
                        
                        # --- KRİTİK KONTROL ---
                        # Sayı 1 veya daha büyükse listeye ekle
                        if count >= 1:
                            print(f"--> BINGO! Aktif yemek bulundu: {count} adet")
                            toplam_yemek_sayisi += count
                            # Restoran ismini alıp listeye ekleyelim (ilk satır genelde isimdir)
                            restoran_adi = text.splitlines()[1] if len(text.splitlines()) > 1 else "Bilinmiyor"
                            bulunan_restoranlar.append(f"{restoran_adi} ({count} adet)")
                        else:
                            print(f"    İzmir restoranı var ama yemek sayısı: {count} (Mail atılmayacak)")
                except Exception as e:
                    print(f"    Veri okunurken hata: {e}")

        # --- SONUÇ ---
        # Eğer toplam yemek sayısı 1 veya daha fazlaysa mail at
        if toplam_yemek_sayisi >= 1:
            detay_mesaji = "\n".join(bulunan_restoranlar)
            print(f"SONUÇ: Toplam {toplam_yemek_sayisi} yemek bulundu. Mail gönderiliyor.")
            
            send_mail(
                f"MÜJDE: İzmir'de {toplam_yemek_sayisi} Adet Yemek Yakalandı!", 
                f"Koş! Aşağıdaki yerlerde yemek var:\n\n{detay_mesaji}\n\nHemen al: https://getodi.com/student/"
            )
        else:
            print("SONUÇ: İzmir restoranları tarandı, ancak aktif yemek (>=1) bulunamadı.")

        browser.close()

if __name__ == "__main__":
    run()
