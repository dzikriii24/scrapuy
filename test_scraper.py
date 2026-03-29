from scraper import InstagramScraper

print("Testing InstagramScraper setup_driver...")
try:
    scraper = InstagramScraper("Test_User", "test_dir")
    scraper.setup_driver()
    print("SUCCESS: Chrome Driver initialized correctly via Selenium Manager!")
    scraper.driver.quit()
except Exception as e:
    print(f"FAILED: {e}")
