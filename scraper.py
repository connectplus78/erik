import json
import asyncio
from urllib.parse import urljoin
from playwright.async_api import async_playwright

async def run_scraper():
    async with async_playwright() as p:
        # Cloudflare gibi bot korumalarını aşmayı kolaylaştırmak için
        # headless=False yapıp tarayıcının görünmesini sağlayabilirsiniz (Test aşamasında önerilir)
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        target_url = "https://www.hdfilmcehennemi.nl/"
        print(f"Bağlanılıyor: {target_url}")
        
        try:
            # Sayfaya git
            await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            
            # İçeriğin tam yüklenmesi için biraz bekleyelim
            await page.wait_for_timeout(6000)

            films = []
            
            # Sitenin güncel yapısına göre film kartı seçicileri
            # Genellikle posterlerin olduğu 'a' etiketleri hedeflenir
            film_elements = await page.locator(".poster-container a, .film-box a, .card a, .ml-item a").all()

            if not film_elements:
                print("Belirtilen seçicilerle öğe bulunamadı, alternatif aranıyor...")
                film_elements = await page.locator("a.film-item, div.poster a").all()

            print(f"İşlenecek {len(film_elements)} adet bağlantı aday eleman bulundu.")

            for elem in film_elements[:20]: # İlk 20 film
                link = await elem.get_attribute("href")
                title = await elem.get_attribute("title")
                
                if not title:
                    # Alternatif olarak içerisindeki metni veya görselin alt etiketini alalım
                    img_elem = elem.locator("img")
                    if await img_elem.count() > 0:
                        title = await img_elem.get_attribute("alt")
                    else:
                        title = await elem.inner_text()

                if link:
                    # urljoin sayesinde ana domain ilerelative linkler kusursuz birleşir (.nl / .now farkı ortadan kalkar)
                    full_url = urljoin(target_url, link)
                    
                    films.append({
                        "title": title.strip() if title else "Bilinmiyor",
                        "url": full_url
                    })

            # Benzersiz filmleri listele (tekrar edenleri önlemek için)
            unique_films = [dict(t) for t in {tuple(d.items()) for d in films}]

            print(f"Toplam {len(unique_films)} benzersiz film başarıyla çekildi.")

            # JSON dosyasına kaydet
            with open("films_output.json", "w", encoding="utf-8") as f:
                json.dump(unique_films, f, ensure_ascii=False, indent=4)
            print("Veriler 'films_output.json' dosyasına kaydedildi.")

        except Exception as e:
            print(f"Hata oluştu: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
