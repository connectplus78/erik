import json
import os
import re
import base64
import codecs
import time
from bs4 import BeautifulSoup
from curl_cffi import requests

BASE_URL = "https://www.fullhdfilmizlesene.life"
DB_FILE = "veritabani.json"

KATEGORILER = {
    "En Çok İzlenen Filmler": "/en-cok-izlenen-filmler-izle-hd/",
    "IMDB Puanı Yüksek Filmler": "/filmizle/imdb-puani-yuksek-filmler-izle-1/",
    "Aile Filmleri": "/filmizle/aile-filmleri-hdf-izle/",
    "Aksiyon Filmleri": "/filmizle/aksiyon-filmleri-hdf-izle/",
    "Animasyon Filmleri": "/filmizle/animasyon-filmleri-fhd-izle/",
    "Belgeseller": "/filmizle/belgesel-filmleri-izle/",
    "Bilim Kurgu Filmleri": "/filmizle/bilim-kurgu-filmleri-izle-2/",
    "Blu Ray Filmler": "/filmizle/bluray-filmler-izle/",
    "Çizgi Filmler": "/filmizle/cizgi-filmler-fhd-izle/",
    "Dram Filmleri": "/filmizle/dram-filmleri-hd-izle/",
    "Fantastik Filmler": "/filmizle/fantastik-filmler-hd-izle/",
    "Gerilim Filmleri": "/filmizle/gerilim-filmleri-fhd-izle/",
    "Gizem Filmleri": "/filmizle/gizem-filmleri-hd-izle/",
    "Hint Filmleri": "/filmizle/hint-filmleri-fhd-izle/",
    "Komedi Filmleri": "/filmizle/komedi-filmleri-fhd-izle/",
    "Korku Filmleri": "/filmizle/korku-filmleri-izle-3/",
    "Macera Filmleri": "/filmizle/macera-filmleri-fhd-izle/",
    "Müzikal Filmler": "/filmizle/muzikal-filmler-izle/",
    "Polisiye Filmleri": "/filmizle/polisiye-filmleri-izle/",
    "Psikolojik Filmler": "/filmizle/psikolojik-filmler-izle/",
    "Romantik Filmleri": "/filmizle/romantik-filmleri-fhd-izle/",
    "Savaş Filmleri": "/filmizle/savas-filmleri-fhd-izle/",
    "Suç Filmleri": "/filmizle/suc-filmleri-izle/",
    "Tarih Filmleri": "/filmizle/tarih-filmleri-fhd-izle/",
    "Western Filmler": "/filmizle/western-filmler-hd-izle-3/",
    "Yerli Filmler": "/filmizle/yerli-filmler-hd-izle/"
}

PROXY = {"http": "socks5h://127.0.0.1:40000", "https": "socks5h://127.0.0.1:40000"}

session = requests.Session(impersonate="chrome120", proxies=PROXY)
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8"
})

def decode_iframe(s):
    if not isinstance(s, str) or len(s) < 10: return None
    s = s.strip()
    if s.startswith("//"): return "https:" + s
    if s.startswith("http"): return s
    s_pad = s + '=' * (-len(s) % 4)
    for method in ['rot13_b64', 'b64']:
        try:
            dec = base64.b64decode(codecs.encode(s_pad, 'rot_13')).decode('utf-8') if method == 'rot13_b64' else base64.b64decode(s_pad).decode('utf-8')
            if "http" in dec and ("vod" in dec or "embed" in dec or "player" in dec): return dec.replace("\\/", "/")
        except: pass
    return None

def extract_movie_data(film_url):
    try:
        req = session.get(film_url, timeout=15)
        soup = BeautifulSoup(req.text, 'html.parser')
        
        aciklama = ""
        ozet_div = soup.select_one(".ozet, .summary, .film-ozeti, div[itemprop='description'], p[itemprop='description']")
        if ozet_div: aciklama = ozet_div.text.strip()
        
        if not aciklama or len(aciklama) < 10:
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc: aciklama = meta_desc.get("content", "").strip()
                
        iframe_linki = None
        scx_match = re.search(r'(?:scx|data)\s*=\s*(\{.*?\});', req.text)
        if scx_match:
            encoded_strings = re.findall(r"'(.*?)'", str(json.loads(scx_match.group(1))))
            for code in encoded_strings:
                dec = decode_iframe(code)
                if dec: 
                    iframe_linki = dec
                    break
        return {"aciklama": aciklama or "Açıklama yok.", "iframe": iframe_linki}
    except: return {"aciklama": "Hata", "iframe": None}

def bot_calistir():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            veritabani = json.load(f)
    else:
        veritabani = {"kategoriler": list(KATEGORILER.keys()), "filmler": []}

    mevcut_basliklar = [film["baslik"] for film in veritabani.get("filmler", [])]
    
    for kategori_adi, url_yolu in KATEGORILER.items():
        print(f"\n>> Taraniyor: {kategori_adi}")
        sayfa_url = BASE_URL + url_yolu
        
        while sayfa_url:
            try:
                print(f"  > Sayfa: {sayfa_url}")
                req = session.get(sayfa_url, timeout=20)
                soup = BeautifulSoup(req.content, 'html.parser')
                film_listesi = soup.select("li.film, div.movie-item, article.film, .movie-list li")
                
                if not film_listesi: break

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
                        print(f"    ✅ Eklendi: {baslik}")

                # SAYFALAMA: "a.next" yerine sitenin kullandığı "İleri" butonunun class'ını buraya yazın
                next_page = soup.select_one("a.next, .pagination-next a")
                if next_page and next_page.get("href"):
                    sayfa_url = next_page.get("href")
                    if not sayfa_url.startswith("http"): sayfa_url = BASE_URL + sayfa_url
                    time.sleep(2)
                else:
                    sayfa_url = None
            except Exception as e:
                print(f"  [!] Hata: {e}")
                break

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(veritabani, f, ensure_ascii=False, indent=4)
    print("\n🎉 İşlem tamamlandı! Veritabanı güncel.")

if __name__ == "__main__":
    bot_calistir()
