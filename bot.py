def bot_calistir():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            veritabani = json.load(f)
    else:
        veritabani = {"kategoriler": list(KATEGORILER.keys()), "filmler": []}

    mevcut_basliklar = [film["baslik"] for film in veritabani.get("filmler", [])]
    
    for kategori_adi, url_yolu in KATEGORILER.items():
        print(f"\n>> Taraniyor: {kategori_adi}")
        sayfa = 1
        
        while True:
            # URL yapısını otomatik oluşturur: /kategori/page/1/, /kategori/page/2/
            # Eğer sitenizde '/page/' yoksa, URL yapısını ona göre düzeltiriz.
            sayfa_url = f"{BASE_URL}{url_yolu.rstrip('/')}/page/{sayfa}/"
            
            print(f"  > Taranan Sayfa: {sayfa_url}")
            try:
                req = session.get(sayfa_url, timeout=20)
                if req.status_code != 200:
                    print("    [!] Sayfa bulunamadı (sonuna gelindi).")
                    break

                soup = BeautifulSoup(req.content, 'html.parser')
                film_listesi = soup.select("li.film, div.movie-item, article.film, .movie-list li")
                
                # Sayfada hiç film yoksa döngüden çık
                if not film_listesi:
                    print("    [!] Film bulunamadı, kategori bitti.")
                    break

                for li in film_listesi:
                    baslik_elem = li.select_one("span.film-title, h2.title, a.title")
                    if not baslik_elem: continue
                    baslik = baslik_elem.text.strip()
                    
                    if baslik in mevcut_basliklar: continue
                    
                    link_elem = li.select_one("a")
                    film_url = link_elem.get("href")
                    if not film_url.startswith("http"): film_url = BASE_URL + film_url
                    
                    detay = extract_movie_data(film_url)
                    if detay["iframe"]:
                        veritabani["filmler"].append({
                            "id": len(veritabani["filmler"]) + 1,
                            "baslik": baslik,
                            "kategori": kategori_adi,
                            "iframe": detay["iframe"],
                            "aciklama": detay["aciklama"]
                        })
                        mevcut_basliklar.append(baslik)
                        print(f"      ✅ Eklendi: {baslik}")

                sayfa += 1
                time.sleep(1.5) # Sunucuyu yormamak için kısa bekleme
            except Exception as e:
                print(f"    [!] Hata: {e}")
                break

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(veritabani, f, ensure_ascii=False, indent=4)
    print("\n🎉 Tüm sayfalar tarandı, veritabanı güncellendi!")
