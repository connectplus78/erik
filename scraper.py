import json
import asyncio
from playwright.async_api import async_playwright

async def run_scraper():
    async with async_playwright() as p:
        # Tarayıcıyı headless (arayüzsüz) modda başlatıyoruz
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        target_url = "https://www.hdfilmcehennemi.now/"
        print(f"Bağlanılıyor: {target_url}")
        
        try:
            # Sayfaya git ve yüklenmesini bekle
            await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            
            # Cloudflare veya benzeri geçişler için kısa bir bekleme
            await page.wait_for_timeout(5000)

            # Örnek olarak ana sayfadaki film kartlarını/başlıklarını çekme
            # Sitenin güncel HTML yapısına göre seçici (selector) güncellenebilir
            films = []
            film_elements = await page.locator(".poster-container, .film-box, .card").all()
            
            if not film_elements:
                # Alternatif genel link yakalama
                film_elements = await page.locator("a.film-item, .list-movie a").all()

            for elem in film_elements[:20]: # İlk 20 filmi örnek alalım
                title = await elem.get_attribute("title")
                link = await elem.get_attribute("href")
                if not title:
                    title = await elem.inner_text()
                
                if link:
                    films.append({
                        "title": title.strip() if title else "Bilinmiyor",
                        "url": link if link.startswith("http") else f"https://www.hdfilmcehennemi.now{link}"
                    })

            print(f"Toplam {len(films)} film bulundu.")

            # Elde edilen verileri JSON dosyasına kaydet
            with open("films_output.json", "w", encoding="utf-8") as f:
                json.dump(films, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Hata oluştu: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
