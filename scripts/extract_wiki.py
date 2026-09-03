# scripts/extract_wiki.py
import requests
import json
import os
import time
from bs4 import BeautifulSoup

# Konfigurasi
REPO_OWNER = "Fikaramandio"
REPO_NAME = "korpus-bahasa-Gayo"
WIKI_BASE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/wiki"
OUTPUT_FILE = "data/raw/wiki_pages_all.json"

def get_all_page_titles():
    """Mengambil semua judul halaman dari halaman _pages."""
    print("📋 Mengambil daftar semua halaman dari _pages...")
    
    pages_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/wiki/_pages"
    print(f"🔍 Mengambil dari: {pages_url}")
    
    try:
        response = requests.get(pages_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        titles = []
        # Cari semua link yang mengarah ke halaman wiki
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Pola: /wiki/Nama_Halaman (bukan /wiki/_pages atau /wiki/Home)
            if href.startswith('/wiki/') and not href.startswith('/wiki/_'):
                title = href.replace('/wiki/', '').strip('/')
                # Filter halaman non-entri
                skip_titles = ['Home', 'Tata-bahasa', 'tata-bahasa', 'F', 'Q', 'V', 'X']
                if title and title not in skip_titles:
                    titles.append(title)
        
        # Hapus duplikat
        titles = list(set(titles))
        print(f"📄 Ditemukan {len(titles)} halaman.")
        return titles
    except Exception as e:
        print(f"❌ Gagal mengambil daftar halaman: {e}")
        return []

def fetch_page_content(title):
    """Mengambil konten dari sebuah halaman wiki."""
    url = f"{WIKI_BASE_URL}/{title.replace(' ', '-')}"
    print(f"📥 Mengambil: {title}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find('div', class_='markdown-body')
        if content_div:
            return {
                "title": title,
                "html": str(content_div),
                "text": content_div.get_text(separator="\n", strip=True),
                "url": url,
                "success": True
            }
        else:
            return {"title": title, "success": False, "error": "Konten tidak ditemukan"}
    except Exception as e:
        return {"title": title, "success": False, "error": str(e)}

def save_data(data, filename):
    """Menyimpan data ke file JSON."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Data disimpan ke: {filename}")

def main():
    print("🚀 Memulai ekstraksi semua halaman wiki...")
    
    titles = get_all_page_titles()
    if not titles:
        print("⚠️  Tidak ada halaman ditemukan.")
        print("💡 Pastikan halaman _pages dapat diakses.")
        print("   Coba buka: https://github.com/Fikaramandio/korpus-bahasa-Gayo/wiki/_pages")
        return
    
    print(f"📄 Total halaman: {len(titles)}")
    
    all_pages = []
    failed = []
    
    for i, title in enumerate(titles, 1):
        print(f"\n🔄 [{i}/{len(titles)}]")
        result = fetch_page_content(title)
        if result.get("success"):
            all_pages.append(result)
        else:
            failed.append(title)
            print(f"⚠️  Gagal: {title}")
        time.sleep(0.3)
    
    save_data(all_pages, OUTPUT_FILE)
    
    if failed:
        with open("data/failed_pages.json", 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)
        print(f"⚠️  {len(failed)} halaman gagal diambil.")
    
    print(f"\n✅ Selesai! Berhasil mengambil {len(all_pages)} dari {len(titles)} halaman.")

if __name__ == "__main__":
    main()