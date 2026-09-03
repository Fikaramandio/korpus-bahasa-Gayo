# scripts/extract_from_local.py
import os
import json
import re
from pathlib import Path

# Konfigurasi
WIKI_DIR = "D:/korpus-bahasa-Gayo.wiki"
OUTPUT_FILE = "data/raw/wiki_pages_all.json"

def get_all_page_files():
    """Mengambil semua file .md dari folder wiki lokal."""
    wiki_path = Path(WIKI_DIR)
    if not wiki_path.exists():
        print(f"❌ Folder tidak ditemukan: {WIKI_DIR}")
        return []
    
    # Cari semua file .md
    md_files = list(wiki_path.glob("*.md"))
    print(f"📄 Ditemukan {len(md_files)} file .md")
    return md_files

def extract_title_from_filename(filename):
    """Mengambil judul dari nama file."""
    # Hapus ekstensi .md
    title = filename.stem
    # Ganti underscore dengan spasi (jika ada)
    title = title.replace('_', ' ')
    return title

def parse_markdown_content(content, title):
    """Mengurai konten markdown menjadi struktur."""
    # Cari bagian yang dimulai dengan "## " atau "### "
    lines = content.split('\n')
    
    # Cari header utama
    header = None
    for i, line in enumerate(lines):
        if line.startswith('## ') or line.startswith('### '):
            header = line.strip('# ')
            break
    
    # Jika tidak ada header, gunakan judul dari filename
    if not header:
        header = title
    
    return {
        "title": title,
        "html": content,  # Simpan sebagai markdown mentah
        "text": content,
        "url": f"local://{title}",
        "success": True,
        "source": "local"
    }

def save_data(data, filename):
    """Menyimpan data ke file JSON."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Data disimpan ke: {filename}")

def main():
    print("🚀 Memulai ekstraksi dari folder lokal...")
    
    files = get_all_page_files()
    if not files:
        print("⚠️  Tidak ada file ditemukan.")
        return
    
    all_pages = []
    failed = []
    
    for i, file_path in enumerate(files, 1):
        print(f"\n🔄 [{i}/{len(files)}] Membaca: {file_path.name}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            title = extract_title_from_filename(file_path)
            # Skip halaman non-entri
            skip_titles = ['Home', '_Sidebar', '_Footer', 'Tata-bahasa', 'F', 'Q', 'V', 'X']
            if title in skip_titles:
                print(f"⏭️  Dilewati: {title}")
                continue
            
            page_data = parse_markdown_content(content, title)
            all_pages.append(page_data)
        except Exception as e:
            failed.append(file_path.name)
            print(f"⚠️  Gagal membaca {file_path.name}: {e}")
    
    save_data(all_pages, OUTPUT_FILE)
    
    if failed:
        with open("data/failed_pages_local.json", 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)
        print(f"⚠️  {len(failed)} file gagal dibaca.")
    
    print(f"\n✅ Selesai! Berhasil mengambil {len(all_pages)} dari {len(files)} file.")

if __name__ == "__main__":
    main()