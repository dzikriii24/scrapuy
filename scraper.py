import os
import time
import requests
import yt_dlp
import hashlib
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

class InstagramScraper:
    def __init__(self, nim_nama, base_dir):
        self.nim_nama = nim_nama
        self.base_dir = base_dir
        self.driver = None
        self.progress_callback = None
        
    def setup_driver(self):
        """Setup Chrome driver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def create_folder_structure(self, username):
        """Buat struktur folder untuk satu akun"""
        folder_name = f"{self.nim_nama}_{username.replace('.', '_')}"
        paths = {
            'image': os.path.join(self.base_dir, 'image', folder_name),
            'text': os.path.join(self.base_dir, 'text', folder_name),
            'audio': os.path.join(self.base_dir, 'audio', folder_name)
        }
        for path in paths.values():
            os.makedirs(path, exist_ok=True)
        return paths
        
    def get_feed_links(self, username, limit=90):
        """Ambil link postingan feed"""
        url = f"https://www.instagram.com/{username}/"
        print(f"  🌐 Membuka profile: {url}")
        self.driver.get(url)
        time.sleep(5)
        
        post_links = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        
        while scroll_attempts < 15 and len(post_links) < limit:
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
            for link in links:
                href = link.get_attribute("href")
                if href and "/p/" in href:
                    clean_url = href.split('?')[0]
                    if clean_url not in post_links:
                        post_links.append(clean_url)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
            
        return post_links[:limit]
    
    def get_reel_links(self, username, limit=20):
        """Ambil link reels dari tab REELS"""
        url = f"https://www.instagram.com/{username}/reels/"
        print(f"  🎬 Membuka tab reels: {url}")
        self.driver.get(url)
        time.sleep(5)
        
        reel_links = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        
        while scroll_attempts < 15 and len(reel_links) < limit:
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/reel/')]")
            for link in links:
                href = link.get_attribute("href")
                if href and "/reel/" in href:
                    clean_url = href.split('?')[0]
                    if clean_url not in reel_links:
                        reel_links.append(clean_url)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
            
        return reel_links[:limit]
    
    def get_caption(self):
        """Ambil caption dari postingan"""
        try:
            time.sleep(2)
            caption = ""
            selectors = [
                "div._a9zr",
                "div._a9zr div._a9zs", 
                "div._a9zr span._ap3a",
                "div.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x193iq5w.x1swvt13.x1f6kntn",
                "div[role='dialog'] div._a9zr",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text
                    if text and len(text) > 10:
                        if not text.startswith("like") and not "likes" in text.lower():
                            if not text.startswith("view all"):
                                caption = text
                                break
                if caption:
                    break
            
            if not caption:
                try:
                    meta_desc = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:description']")
                    caption = meta_desc.get_attribute("content")
                except:
                    pass
                    
            return caption or "[Caption tidak tersedia]"
        except:
            return "[Gagal mengambil caption]"
    
    def capture_post_image(self, save_path, slide_target=None):
        """Screenshot gambar postingan"""
        try:
            if slide_target and slide_target > 1:
                for i in range(slide_target - 1):
                    try:
                        next_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next']")
                        if next_btn.is_enabled():
                            next_btn.click()
                            time.sleep(1.5)
                    except:
                        break
            
            selectors = [
                "div[role='dialog'] article img",
                "div[role='dialog'] div.x5yr21d img",
                "article div._aagv img",
                "div._aagu img",
                "img[style*='object-fit']"
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    src = elem.get_attribute("src")
                    if src and "profile" not in src.lower() and "avatar" not in src.lower():
                        elem.screenshot(save_path)
                        if os.path.getsize(save_path) > 5000:
                            return True
            return False
        except:
            return False
    
    def download_video_with_ytdlp(self, video_url, save_path):
        """Download video menggunakan yt-dlp"""
        try:
            ydl_opts = {
                'outtmpl': save_path,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'format': 'best',
                'http_client': 'urllib',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return os.path.exists(save_path) and os.path.getsize(save_path) > 10000
        except Exception as e:
            print(f"      ❌ yt-dlp error: {e}")
            return False
    
    def process_feed(self, post_url, paths, counters, target_images, target_texts):
        """Proses satu postingan feed"""
        self.driver.get(post_url)
        time.sleep(5)
        
        shortcode = post_url.split('/')[-2]
        print(f"    📌 Post: {shortcode}")
        
        # Ambil caption
        if counters['text'] < target_texts:
            caption = self.get_caption()
            text_path = os.path.join(paths['text'], f"post_{counters['text']+1}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"URL: {post_url}\n\n{caption}")
            counters['text'] += 1
            print(f"      📝 Teks ke-{counters['text']}")
            
            if self.progress_callback:
                self.progress_callback({'captions': counters['text']})
        
        # Ambil gambar
        if counters['image'] < target_images:
            url_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
            img_path = os.path.join(paths['image'], f"image_{counters['image']+1}_{url_hash}.jpg")
            
            if self.capture_post_image(img_path):
                counters['image'] += 1
                size = os.path.getsize(img_path) / 1024
                print(f"      🖼️ Gambar ke-{counters['image']} ({size:.1f} KB)")
                
                if self.progress_callback:
                    self.progress_callback({'images': counters['image']})
            
            # Carousel navigation
            slide_count = 1
            while slide_count < 15 and counters['image'] < target_images:
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next']")
                    if next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(2)
                        slide_count += 1
                        
                        url_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
                        img_path = os.path.join(paths['image'], f"image_{counters['image']+1}_{url_hash}.jpg")
                        
                        if self.capture_post_image(img_path):
                            counters['image'] += 1
                            size = os.path.getsize(img_path) / 1024
                            print(f"      🖼️ Gambar ke-{counters['image']} ({size:.1f} KB)")
                            
                            if self.progress_callback:
                                self.progress_callback({'images': counters['image']})
                    else:
                        break
                except:
                    break
    
    def process_reel(self, reel_url, paths, counters, target_videos):
        """Proses satu reels"""
        self.driver.get(reel_url)
        time.sleep(5)
        
        shortcode = reel_url.split('/')[-2]
        print(f"    🎬 Reel: {shortcode}")
        
        # Ambil caption
        if counters['text'] < target_videos * 2:
            caption = self.get_caption()
            text_path = os.path.join(paths['text'], f"post_{counters['text']+1}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"URL: {reel_url}\n\n{caption}")
            counters['text'] += 1
            print(f"      📝 Teks ke-{counters['text']}")
            
            if self.progress_callback:
                self.progress_callback({'captions': counters['text']})
        
        # Download video
        if counters['video'] < target_videos:
            video_path = os.path.join(paths['audio'], f"video_{counters['video']+1}.mp4")
            print(f"      🎬 Download video...")
            
            if self.download_video_with_ytdlp(reel_url, video_path):
                counters['video'] += 1
                size = os.path.getsize(video_path) / 1024
                print(f"      ✅ Video ke-{counters['video']} ({size:.1f} KB)")
                
                if self.progress_callback:
                    self.progress_callback({'videos': counters['video']})
            else:
                print(f"      ❌ Gagal download video")
    
    def scrape_account(self, username, target_images, target_texts, target_videos, progress_callback=None):
        """Scrape satu akun"""
        self.progress_callback = progress_callback
        paths = self.create_folder_structure(username)
        counters = {'image': 0, 'text': 0, 'video': 0}
        
        # Ambil feeds untuk gambar dan caption
        print(f"\n📸 Mengambil feeds dari @{username}...")
        feed_links = self.get_feed_links(username, limit=target_images)
        
        for idx, post_url in enumerate(feed_links, 1):
            if counters['image'] >= target_images and counters['text'] >= target_texts:
                break
            print(f"\n    [{idx}/{len(feed_links)}] Processing feed...")
            self.process_feed(post_url, paths, counters, target_images, target_texts)
            time.sleep(1)
        
        # Ambil reels untuk video
        if target_videos > 0:
            print(f"\n🎬 Mengambil reels dari @{username}...")
            reel_links = self.get_reel_links(username, limit=target_videos + 5)
            
            for idx, reel_url in enumerate(reel_links, 1):
                if counters['video'] >= target_videos:
                    break
                print(f"\n    [{idx}/{len(reel_links)}] Processing reel...")
                self.process_reel(reel_url, paths, counters, target_videos)
                time.sleep(2)
        
        print(f"\n  📊 Hasil {username}: {counters['image']} gambar, {counters['text']} caption, {counters['video']} video")
        return counters