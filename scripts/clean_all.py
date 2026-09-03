# scripts/clean_all.py - Perbaikan untuk menangani halaman tanpa Salabisasi/Kelas kata
import json
import os
import re

INPUT_FILE = "data/raw/wiki_pages_all.json"
OUTPUT_FILE = "data/kamus_terstruktur_all.json"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'__', '', text)
    text = re.sub(r'_{2,}', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^:\s*', '', text)
    return text.strip()

def is_dictionary_page(text, title):
    """Memeriksa apakah halaman adalah entri kamus."""
    # Skip halaman daftar isi (satu huruf)
    if len(title) == 1 and title.isalpha():
        return False
    
    skip_titles = ['Home', 'Tata-bahasa', 'tata-bahasa', 'F', 'Q', 'V', 'X']
    if title in skip_titles:
        return False
    
    # Cek apakah ada marker entri kamus
    markers = ["Salabisasi", "Kelas kata", "Kelas Kata", "Makna", "Contoh", 
               "nomina", "verba", "adjektiva", "konjungsi"]
    has_marker = any(marker in text for marker in markers)
    
    # Jika tidak ada marker formal, cek apakah ada definisi (angka/bullet)
    if not has_marker:
        # Cek pola definisi seperti "1. ..." atau "- ..." atau "**_Abang_**"
        definition_patterns = [
            r'\d+\.\s+',           # Angka diikuti titik
            r'[-*]\s+',            # Bullet point
            r'\*\*[^*]+\*\*',      # Teks tebal
            r'[Ss]audara',         # Kata "saudara"
            r'[Ss]ebutan',         # Kata "sebutan"
        ]
        has_definition = any(re.search(pattern, text) for pattern in definition_patterns)
        if has_definition and len(text) > 50:
            return True
    
    return has_marker

def extract_definitions_from_text(text, title):
    """Ekstrak definisi dari teks yang tidak memiliki struktur formal."""
    definitions = []
    
    # Cari pola: "1. definisi", "2. definisi", dst
    numbered_matches = re.findall(r'(\d+)\.\s+([^\n]+)', text)
    if numbered_matches:
        for num, def_text in numbered_matches:
            definitions.append(clean_text(def_text))
        return definitions
    
    # Cari pola: "* _kata_: definisi" atau "- kata: definisi"
    bullet_matches = re.findall(r'[-*]\s+_\s*([^_]+)_\s*:\s*([^\n]+)', text)
    if not bullet_matches:
        bullet_matches = re.findall(r'[-*]\s+([^:]+):\s+([^\n]+)', text)
    if bullet_matches:
        for key, value in bullet_matches:
            definitions.append(clean_text(f"{key}: {value}"))
        return definitions
    
    # Cari pola: "kata: definisi" (tanpa bullet)
    col_matches = re.findall(r'^([^:]+):\s+([^\n]+)', text, re.MULTILINE)
    if col_matches:
        for key, value in col_matches[:5]:  # Ambil maksimal 5 definisi
            definitions.append(clean_text(f"{key}: {value}"))
        return definitions
    
    # Jika tidak ada, ambil paragraf pertama yang bukan judul
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and len(line) > 20:
            definitions.append(clean_text(line))
            break
    
    return definitions

def parse_wiki_entry(text, title):
    """Mengurai entri kamus dengan pendekatan fleksibel."""
    if not is_dictionary_page(text, title):
        return None
    
    entry = {
        "kata": title,
        "ejaan_alternatif": None,
        "suku_kata": None,
        "kelas_kata": None,
        "makna": [],
        "contoh": [],
        "catatan": None,
        "sumber": "Hazeu (1907)",
        "status": "perlu_verifikasi"
    }
    
    # 1. Ejaan alternatif
    alt_match = re.search(r'\(atau\s*\*{0,2}_{0,2}([^)]+?)\*{0,2}_{0,2}\)', text)
    if alt_match:
        entry['ejaan_alternatif'] = clean_text(alt_match.group(1))
    
    # 2. Suku kata
    salab_match = re.search(r'Salabisasi\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if salab_match:
        entry['suku_kata'] = clean_text(salab_match.group(1))
    
    # 3. Kelas kata
    kelas_match = re.search(r'Kelas\s*[Kk]ata\s*:\s*([^\n]+)', text)
    if kelas_match:
        entry['kelas_kata'] = clean_text(kelas_match.group(1))
    
    # 4. Makna - coba berbagai pendekatan
    makna_content = extract_section(text, "Makna", ["Contoh", "Catatan", "Konteks", "###"])
    if not makna_content:
        makna_match = re.search(r'Makna\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if makna_match:
            makna_content = clean_text(makna_match.group(1))
    
    # Jika masih tidak ada, gunakan ekstraktor definisi
    if not makna_content:
        definitions = extract_definitions_from_text(text, title)
        if definitions:
            entry['makna'] = definitions
            # Coba tentukan kelas kata dari teks
            if 'nomina' in text.lower() or 'kata benda' in text.lower():
                entry['kelas_kata'] = 'Nomina'
            elif 'verba' in text.lower() or 'kata kerja' in text.lower():
                entry['kelas_kata'] = 'Verba'
            elif 'adjektiva' in text.lower() or 'kata sifat' in text.lower():
                entry['kelas_kata'] = 'Adjektiva'
    
    if makna_content and not entry['makna']:
        if '\n' in makna_content:
            points = [clean_text(p) for p in makna_content.split('\n') if p.strip()]
            entry['makna'] = points if len(points) > 1 else [makna_content]
        else:
            entry['makna'] = [makna_content]
    
    # 5. Contoh - cari pola contoh kalimat
    contoh_content = extract_section(text, "Contoh Kalimat", ["Konteks", "###", "##"])
    if not contoh_content:
        contoh_content = extract_section(text, "Contoh", ["Konteks", "###", "##"])
    if not contoh_content:
        # Cari pola: "* _kata_: contoh" atau "* contoh"
        contoh_matches = re.findall(r'[-*]\s+([^:]+):\s+([^\n]+)', text)
        if contoh_matches:
            contoh_content = ' '.join([f"{k}: {v}" for k, v in contoh_matches[:3]])
    
    if contoh_content:
        sentences = re.split(r'(?<=[.!?])\s+', contoh_content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 5]
        entry['contoh'] = sentences[:3] if sentences else []
    
    # 6. Catatan
    catatan_content = extract_section(text, "Catatan", ["Sumber", "##"])
    if catatan_content:
        entry['catatan'] = catatan_content
    
    # 7. Status
    if entry['makna'] and entry['kelas_kata']:
        entry['status'] = 'lengkap'
    elif entry['makna'] or entry['kelas_kata']:
        entry['status'] = 'sebagian'
    
    return entry

def extract_section(text, header, stop_patterns):
    patterns = [
        rf'^\s*{header}\s*:\s*$',
        rf'^\s*{header}\s*:',
        rf'^\s*{header}\s*$',
    ]
    start_pos = None
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            start_pos = match.end()
            break
    if start_pos is None:
        return None
    stop_pattern = re.compile(rf'^\s*(?:{"|".join(stop_patterns)})\s*', re.MULTILINE | re.IGNORECASE)
    stop_match = stop_pattern.search(text, start_pos)
    if stop_match:
        content = text[start_pos:stop_match.start()]
    else:
        content = text[start_pos:]
    content = clean_text(content)
    content = re.sub(r'[•\-*]\s*', '', content)
    return content

def main():
    print("🔄 Memulai pembersihan data (versi dengan fallback untuk halaman tanpa struktur)...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_pages = json.load(f)
    
    print(f"📄 Ditemukan {len(raw_pages)} halaman.")
    
    kamus = []
    skipped = []
    
    for i, page in enumerate(raw_pages, 1):
        if i % 100 == 0:
            print(f"🔄 Memproses halaman {i}/{len(raw_pages)}...")
        
        if not page.get("success", False):
            skipped.append(page.get('title', 'Unknown'))
            continue
        
        title = page.get("title", "")
        text = page.get("text", "")
        
        # Skip halaman daftar isi
        if title in ['Home', 'Tata-bahasa', 'tata-bahasa', 'F', 'Q', 'V', 'X']:
            skipped.append(title)
            continue
        
        if len(title) == 1 and title.isalpha():
            skipped.append(title)
            continue
        
        entry = parse_wiki_entry(text, title)
        if entry and (entry.get('makna') or entry.get('kelas_kata')):
            kamus.append(entry)
        else:
            skipped.append(title)
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(kamus, f, indent=2, ensure_ascii=False)
    
    with open("data/skipped_all.json", 'w', encoding='utf-8') as f:
        json.dump(skipped, f, indent=2, ensure_ascii=False)
    
    stats = {
        "total_halaman": len(raw_pages),
        "entri_kamus": len(kamus),
        "dilewati": len(skipped),
        "status": {
            "lengkap": len([e for e in kamus if e.get("status") == "lengkap"]),
            "sebagian": len([e for e in kamus if e.get("status") == "sebagian"]),
        }
    }
    
    with open("data/statistik_all.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Data disimpan ke: {OUTPUT_FILE}")
    print(f"📊 Statistik:")
    print(f"   - Total halaman: {stats['total_halaman']}")
    print(f"   - Entri kamus: {stats['entri_kamus']}")
    print(f"   - Dilewati: {stats['dilewati']}")
    print(f"   - Status: Lengkap={stats['status']['lengkap']}, Sebagian={stats['status']['sebagian']}")
    print("✅ Selesai!")

if __name__ == "__main__":
    main()