import os
import time
import requests
import urllib.parse
import csv
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class NewsScraper:
    def __init__(self, identitas, base_dir="evaluasi_mbg_berita", headless=True):
        self.identitas = identitas
        self.base_dir = base_dir
        self.headless = headless
        self.main_folder = os.path.join(self.base_dir, self.identitas)
        self.driver = None
        
        os.makedirs(self.main_folder, exist_ok=True)
        
    def setup_driver(self):
        """Inisialisasi Chrome Driver untuk Selenium"""
        print("   🌐 Menyiapkan Browser (Selenium)...")
        options = Options()
        if self.headless:
            options.add_argument('--headless=new') # Menggunakan mode headless terbaru
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Tambahan agar halaman memuat lebih cepat (tidak perlu tunggu gambar penuh)
        options.page_load_strategy = 'eager' 
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"      ❌ Gagal inisialisasi Selenium: {str(e)}")
            return False

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            
    def clean_keyword(self, text):
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        return text.strip()

    def create_folder(self, keyword):
        safe_name = "".join([c if c.isalnum() else "_" for c in keyword])
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        folder_path = os.path.join(self.main_folder, safe_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def get_article_content(self, url):
        """Eksraksi teks berita menggunakan Selenium dengan menunggu Redirect Google"""
        if not self.driver:
            return "[Driver tidak tersedia]"
            
        try:
            # 1. Buka URL Google News
            self.driver.get(url)
            
            # 2. KUNCI UTAMA: Tunggu sampai kita KELUAR dari news.google.com
            wait = WebDriverWait(self.driver, 20)
            try:
                wait.until(lambda driver: "news.google.com" not in driver.current_url)
            except:
                pass # Jika gagal otomatis, kita coba lanjut saja (kadang URL disamarkan)

            # 3. Tunggu sebentar agar website asli selesai merender teks
            time.sleep(3)
            
            # 4. Ambil HTML dari website asli
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Bersihkan elemen pengganggu
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
                element.extract()
                
            # 5. Cari container artikel
            article_body = None
            selectors = [
                'article', 'div.article__content', 'div.detail__body-text', 
                'div.read__content', 'div.post-content', 'div.entry-content',
                'div.story-content', 'div.item-content', 'div.entry-body',
                'div[itemprop="articleBody"]', '.page-content'
            ]
            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    article_body = found
                    break
            
            target = article_body if article_body else soup
            paragraphs = target.find_all('p')
            
            # 6. Filter paragraf (Minimal 50 karakter agar tulisan "Baca juga", dll tidak ikut)
            content_list = []
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 50 and "Baca juga" not in text and "Baca selengkapnya" not in text:
                    content_list.append(text)
            
            content = "\n\n".join(content_list)
            
            # Validasi jika teks masih kosong atau salah sasaran
            if len(content) < 150:
                return f"[Isi berita gagal diekstrak secara utuh. Teks terlalu pendek atau diproteksi. Cek manual link: {self.driver.current_url}]"
            
            return content
            
        except Exception as e:
            return f"[Gagal mengambil isi berita lewat browser: {str(e)}]"

    def scrape_google_news_rss(self, keyword, limit=10):
        clean_kw = self.clean_keyword(keyword)
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_kw)}&hl=id&gl=ID&ceid=ID:id"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        news_list = []
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            items = root.findall('.//channel/item')
            
            total_found = min(limit, len(items))
            if total_found > 0:
                print(f"   ✅ Menemukan {total_found} link berita. Mulai menyedot isi teks lewat browser...")
            
            for i, item in enumerate(items[:limit], 1):
                title = item.find('title').text if item.find('title') is not None else "Tanpa Judul"
                raw_link = item.find('link').text if item.find('link') is not None else "-"
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "-"
                source = item.find('source').text if item.find('source') is not None else "Google News"
                
                print(f"      📄 [{i}/{total_found}] Mengunjungi : {source}...")
                
                # Ekstrak isi menggunakan Selenium
                isi_berita = self.get_article_content(raw_link)
                
                # Dapatkan URL asli yang sudah di-redirect oleh Selenium (bukan link google news lagi)
                final_url = self.driver.current_url if self.driver and "news.google.com" not in self.driver.current_url else raw_link
                
                clean_title = re.sub(r' - [^-]+$', '', title)
                
                news_list.append({
                    'keyword': clean_kw,
                    'judul': clean_title,
                    'media': source,
                    'tanggal': pub_date,
                    'link': final_url, # Menyimpan link asli medianya
                    'isi_berita': isi_berita
                })
                
        except Exception as e:
            print(f"\n      ❌ Gagal mengambil feed: {str(e)}")
            
        return news_list

    def save_details_to_txt(self, folder_path, news_list):
        for i, news in enumerate(news_list, 1):
            filename = os.path.join(folder_path, f"berita_{i:02d}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Keyword Pencarian : {news['keyword']}\n")
                f.write(f"Judul Berita      : {news['judul']}\n")
                f.write(f"Media / Sumber    : {news['media']}\n")
                f.write(f"Tanggal Publish   : {news['tanggal']}\n")
                f.write(f"URL Asli Berita   : {news['link']}\n")
                f.write("-" * 70 + "\n")
                f.write("ISI BERITA:\n")
                f.write("-" * 70 + "\n\n")
                f.write(news['isi_berita'])
                f.write("\n\n" + "-" * 70 + "\n")

def print_banner():
    clear_screen()
    print("="*70)
    print("📰 GOOGLE NEWS SCRAPER PRO - PERFECT SELENIUM EDITION")
    print("="*70)
    print("Fitur: Bypass Google Redirect, Ekstrak Teks Full, Auto-Foldering")
    print("="*70)

def main():
    print_banner()
    
    identitas = input("\n👤 Masukkan NIM & Nama (contoh: 1237050027_DzikriRabbani): ").strip()
    if not identitas:
        identitas = "Unknown_User"
        
    print("\n📝 Masukkan Daftar Nama MBG (Pisahkan dengan koma atau Enter).")
    print("   Catatan: Tekan Enter 2x jika sudah selesai mengetik/paste.")
    print("-" * 50)
    
    keywords_raw = []
    while True:
        line = input()
        if not line.strip():
            break
        if ',' in line:
            keywords_raw.extend([k.strip() for k in line.split(',') if k.strip()])
        else:
            keywords_raw.append(line.strip())

    if not keywords_raw:
        print("\n❌ Keyword tidak boleh kosong. Program dihentikan.")
        return

    limit_input = input("\n🎯 Target jumlah berita per MBG (default 3): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 3

    # Saya buat default False (kelihatan) agar kamu bisa memantau apakah browsernya benar-benar masuk ke web berita
    is_headless = input("\n👁️ Jalankan browser secara tersembunyi/headless? (y/n, default n): ").strip().lower()
    headless = True if is_headless == 'y' else False

    print("\n" + "="*70)
    print(f"✅ Ditemukan {len(keywords_raw)} keyword yang akan diproses.")
    print(f"✅ Target: {limit} berita per keyword.")
    print(f"✅ Browser: {'Headless (Tersembunyi)' if headless else 'Visible (Terlihat)'}")
    confirm = input("✅ Mulai scraping? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("\n⛔ Dibatalkan.")
        return

    scraper = NewsScraper(identitas, headless=headless)
    all_results = []
    
    try:
        if not scraper.setup_driver():
            print("❌ Tidak bisa lanjut tanpa Browser Driver.")
            return

        print("\n🚀 MEMULAI PENCARIAN & EKSTRAKSI BERITA DENGAN SELENIUM...")
        print("="*70)
        
        for i, kw in enumerate(keywords_raw, 1):
            clean_kw = scraper.clean_keyword(kw)
            
            if not clean_kw:
                continue

            print(f"\n🔍 [{i}/{len(keywords_raw)}] Keyword: '{clean_kw}'")
            
            news_data = scraper.scrape_google_news_rss(clean_kw, limit)
            
            if news_data:
                folder_path = scraper.create_folder(clean_kw)
                scraper.save_details_to_txt(folder_path, news_data)
                all_results.extend(news_data)
            else:
                print(f"   ⚠️ Tidak ada berita ditemukan.")

    except KeyboardInterrupt:
        print("\n\n⛔ Proses dihentikan paksa oleh user.")
    except Exception as e:
        print(f"\n❌ Terjadi error pada sistem: {str(e)}")
    finally:
        print("\n🧹 Menutup browser...")
        scraper.close_driver()

    csv_path = os.path.join(scraper.main_folder, 'rekap_semua_berita.csv')
    if all_results:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['keyword', 'judul', 'media', 'tanggal', 'link', 'isi_berita'])
            writer.writeheader()
            
            csv_data = []
            for item in all_results:
                row = item.copy()
                if len(row['isi_berita']) > 500:
                    row['isi_berita'] = row['isi_berita'][:500] + "... [Selengkapnya di file TXT]"
                csv_data.append(row)
                
            writer.writerows(csv_data)

    print("\n" + "="*70)
    print("🎉 SCRAPING SELESAI!")
    print("="*70)
    print(f"📊 Total Keyword   : {len(keywords_raw)}")
    print(f"📰 Total Berita    : {len(all_results)}")
    print(f"📁 Folder Output   : {os.path.abspath(scraper.main_folder)}")
    print(f"📄 Rekap CSV       : Tersimpan")
    print(f"📝 Detail TXT      : Tersimpan di dalam folder masing-masing")
    print("="*70)

if __name__ == "__main__":
    main()