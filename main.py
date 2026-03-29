import os
import time
from scraper import InstagramScraper

def print_banner():
    print("="*70)
    print("🚀 INSTAGRAM SCRAPER PRO - FULL VERSION")
    print("="*70)
    print("Fitur: Download Gambar, Caption, dan Video dari Instagram")
    print("Support: Multi akun, Carousel, Reels")
    print("="*70)

def get_user_input():
    """Mengambil input dari user"""
    print("\n📝 SILAKAN ISI KONFIGURASI BERIKUT:")
    print("-"*50)
    
    nim_nama = input("NIM & Nama (contoh: 1237050027_DzikriRabbani): ").strip()
    while not nim_nama:
        nim_nama = input("NIM & Nama tidak boleh kosong: ").strip()
    
    usernames_input = input("Username Target (pisah dengan koma, contoh: user1, user2, user3): ").strip()
    usernames = [u.strip() for u in usernames_input.split(',') if u.strip()]
    while not usernames:
        usernames_input = input("Username target tidak boleh kosong: ").strip()
        usernames = [u.strip() for u in usernames_input.split(',') if u.strip()]
    
    print("\n📊 TARGET PER AKUN:")
    print("-"*30)
    
    target_images = input("Target Gambar (default 30, max 100): ").strip()
    target_images = int(target_images) if target_images.isdigit() and 1 <= int(target_images) <= 100 else 30
    
    target_texts = input("Target Caption (default 20, max 100): ").strip()
    target_texts = int(target_texts) if target_texts.isdigit() and 1 <= int(target_texts) <= 100 else 20
    
    target_videos = input("Target Video (default 10, max 30): ").strip()
    target_videos = int(target_videos) if target_videos.isdigit() and 0 <= int(target_videos) <= 30 else 10
    
    base_dir = input(f"Base Directory (default: evaluasi mbg/raw data): ").strip()
    if not base_dir:
        base_dir = "evaluasi mbg/raw data"
    
    return {
        'nim_nama': nim_nama,
        'usernames': usernames,
        'target_images': target_images,
        'target_texts': target_texts,
        'target_videos': target_videos,
        'base_dir': base_dir
    }

def confirm_config(config):
    """Konfirmasi konfigurasi sebelum mulai"""
    print("\n" + "="*70)
    print("📋 KONFIRMASI KONFIGURASI")
    print("="*70)
    print(f"  NIM & Nama      : {config['nim_nama']}")
    print(f"  Username Target : {', '.join(config['usernames'])} ({len(config['usernames'])} akun)")
    print(f"  Target Gambar   : {config['target_images']} per akun")
    print(f"  Target Caption  : {config['target_texts']} per akun")
    print(f"  Target Video    : {config['target_videos']} per akun")
    print(f"  Base Directory  : {config['base_dir']}")
    print("="*70)
    
    confirm = input("\n✅ Apakah konfigurasi sudah benar? (y/n): ").strip().lower()
    return confirm == 'y'

def show_progress(current, total, account_name, progress_data):
    """Menampilkan progress scraping"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*70)
    print(f"🚀 SCRAPING IN PROGRESS - {current}/{total} Akun")
    print("="*70)
    print(f"📱 Sedang memproses: {account_name}")
    print("-"*50)
    print(f"📸 Gambar: {progress_data.get('images', 0)}")
    print(f"📝 Caption: {progress_data.get('captions', 0)}")
    print(f"🎬 Video: {progress_data.get('videos', 0)}")
    print("-"*50)

def main():
    print_banner()
    
    # Ambil input dari user
    config = get_user_input()
    
    # Konfirmasi konfigurasi
    if not confirm_config(config):
        print("\n🔄 Silakan jalankan ulang program untuk mengubah konfigurasi.")
        return
    
    # Setup
    scraper = InstagramScraper(config['nim_nama'], config['base_dir'])
    total_results = {'images': 0, 'texts': 0, 'videos': 0, 'accounts': {}}
    
    print("\n🔓 MEMBUKA BROWSER...")
    print("="*70)
    print("1. Browser Chrome akan terbuka")
    print("2. Login ke Instagram dengan akun Anda")
    print("3. Setelah login, tekan ENTER untuk melanjutkan")
    print("="*70)
    
    # Setup driver
    scraper.setup_driver()
    scraper.driver.get("https://www.instagram.com/")
    
    input("\n⏎ TEKAN ENTER SETELAH LOGIN MANUAL...")
    
    print("\n✅ Login diterima! Memulai scraping...")
    
    try:
        for idx, username in enumerate(config['usernames'], 1):
            print(f"\n{'='*60}")
            print(f"📱 [{idx}/{len(config['usernames'])}] MEMPROSES: {username}")
            print(f"{'='*60}")
            
            # Progress callback
            def progress_callback(data):
                show_progress(idx, len(config['usernames']), username, data)
            
            # Scrape account
            result = scraper.scrape_account(
                username,
                config['target_images'],
                config['target_texts'],
                config['target_videos'],
                progress_callback=progress_callback
            )
            
            total_results['images'] += result['image']
            total_results['texts'] += result['text']
            total_results['videos'] += result['video']
            total_results['accounts'][username] = result
            
            print(f"\n  ✅ Selesai: {result['image']} gambar, {result['text']} caption, {result['video']} video")
            
            # Delay antar akun
            if idx < len(config['usernames']):
                print(f"\n  ⏱️  Delay 3 detik sebelum akun berikutnya...")
                time.sleep(3)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Proses dihentikan oleh user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        scraper.driver.quit()
    
    # RINGKASAN AKHIR
    print("\n" + "="*70)
    print("🎉 SCRAPING SELESAI!")
    print("="*70)
    print(f"📊 TOTAL KESELURUHAN:")
    print(f"   📸 Gambar : {total_results['images']}")
    print(f"   📝 Caption: {total_results['texts']}")
    print(f"   🎬 Video  : {total_results['videos']}")
    print("\n📱 PER AKUN:")
    for username, result in total_results['accounts'].items():
        print(f"   • @{username}: {result['image']} gambar, {result['text']} caption, {result['video']} video")
    print(f"\n📁 SEMUA FILE TERSIMPAN DI:")
    print(f"   {os.path.abspath(config['base_dir'])}")
    print("="*70)

if __name__ == "__main__":
    # Install dependencies jika diperlukan
    try:
        import yt_dlp
        import selenium
    except ImportError:
        print("📦 Menginstall dependencies...")
        os.system("pip install -r requirements.txt")
    
    main()