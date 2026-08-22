# scripts/extract_wiki_all.py
import requests
import json
import os
import time
from bs4 import BeautifulSoup

# Konfigurasi
REPO_OWNER = "Fikaramandio"
REPO_NAME = "korpus-bahasa-Gayo"
WIKI_BASE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/wiki"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pages"
OUTPUT_FILE = "data/raw/wiki_pages_all.json"

def get_all_page_titles_from_api():
    """Mengambil semua judul halaman menggunakan GitHub API."""
    print("📋 Mengambil daftar semua halaman dari GitHub API...")
    
    # GitHub tidak memiliki API langsung untuk daftar wiki,
    # tapi kita bisa menggunakan halaman "Home" dan mencari semua tautan
    
    # Cara alternatif: menggunakan GitHub Pages API
    # https://api.github.com/repos/{owner}/{repo}/pages
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Halaman utama: {data.get('html_url', 'Tidak ditemukan')}")
    except:
        pass
    
    # Cara utama: scrape halaman "Home" untuk mencari semua tautan
    home_url = f"{WIKI_BASE_URL}/Home"
    print(f"🔍 Mengambil dari: {home_url}")
    
    response = requests.get(home_url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Cari semua tautan ke halaman wiki
    titles = []
    
    # Pola 1: Tautan dengan href="/wiki/Nama_Halaman"
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        # Cari tautan internal wiki
        if href.startswith('/wiki/') and not href.startswith('/wiki/_'):
            title = href.replace('/wiki/', '').strip('/')
            # Filter halaman non-entri
            if title and title not in ['Home', 'Tata-bahasa', 'tata-bahasa', 'F', 'Q', 'V', 'X', '']:
                titles.append(title)
    
    # Hapus duplikat
    titles = list(set(titles))
    
    # Jika tidak ada, coba cara lain: cari link dengan class tertentu
    if not titles:
        print("⚠️  Tidak menemukan tautan dengan pola standar. Mencoba cara alternatif...")
        # Cari semua link yang mengandung "/wiki/"
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/wiki/' in href and not '#ref' in href:
                title = href.split('/wiki/')[-1].strip('/')
                if title and title not in ['Home', 'Tata-bahasa', 'tata-bahasa', 'F', 'Q', 'V', 'X', '']:
                    titles.append(title)
        titles = list(set(titles))
    
    print(f"📄 Ditemukan {len(titles)} halaman.")
    return titles

def get_all_page_titles_from_sidebar():
    """Mengambil daftar halaman dari sidebar GitHub Wiki."""
    # GitHub Wiki memiliki halaman khusus untuk daftar semua halaman
    # https://github.com/{owner}/{repo}/wiki/_pages
    pages_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/wiki/_pages"
    print(f"🔍 Mencoba mengambil dari: {pages_url}")
    
    try:
        response = requests.get(pages_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            titles = []
            
            # Cari elemen dengan daftar halaman
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/wiki/' in href and not href.startswith('/wiki/_'):
                    title = href.split('/wiki/')[-1].strip('/')
                    if title and title not in ['Home', 'Tata-bahasa', 'F', 'Q', 'V', 'X', '']:
                        titles.append(title)
            
            titles = list(set(titles))
            if titles:
                print(f"📄 Ditemukan {len(titles)} halaman.")
                return titles
    except Exception as e:
        print(f"⚠️  Gagal mengambil dari _pages: {e}")
    
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
    except requests.exceptions.RequestException as e:
        return {"title": title, "success": False, "error": str(e)}

def save_data(data, filename):
    """Menyimpan data ke file JSON."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Data disimpan ke: {filename}")

def main():
    print("🚀 Memulai ekstraksi semua halaman wiki...")
    
    # 1. Dapatkan semua judul halaman
    titles = get_all_page_titles_from_api()
    
    # Jika tidak ada, coba dari sidebar
    if not titles:
        titles = get_all_page_titles_from_sidebar()
    
    # Jika masih tidak ada, gunakan daftar manual (contoh)
    if not titles:
        print("⚠️  Tidak dapat menemukan daftar halaman otomatis.")
        print("📝 Menggunakan daftar manual untuk demo...")
        titles = ["Alas", "Belgong", "Anguk"]  # Ganti dengan daftar lengkap nanti
    
    print(f"📄 Total halaman yang akan diekstrak: {len(titles)}")
    
    # 2. Ambil konten setiap halaman
    all_pages = []
    failed = []
    
    for i, title in enumerate(titles, 1):
        print(f"\n🔄 [{i}/{len(titles)}]")
        result = fetch_page_content(title)
        if result.get("success"):
            all_pages.append(result)
        else:
            failed.append(title)
            print(f"⚠️  Gagal: {title} - {result.get('error', '')}")
        time.sleep(0.5)  # Jeda untuk menghindari pembatasan
    
    # 3. Simpan hasil
    save_data(all_pages, OUTPUT_FILE)
    
    # 4. Simpan daftar yang gagal
    if failed:
        with open("data/failed_pages.json", 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)
        print(f"⚠️  {len(failed)} halaman gagal diambil.")
    
    print(f"\n✅ Selesai! Berhasil mengambil {len(all_pages)} dari {len(titles)} halaman.")

if __name__ == "__main__":
    main()