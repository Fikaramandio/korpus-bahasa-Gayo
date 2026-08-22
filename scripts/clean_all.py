# scripts/clean_all.py
import json
import os
import re

INPUT_FILE = "data/raw/wiki_pages_all.json"
OUTPUT_FILE = "data/kamus_terstruktur_all.json"

def clean_text(text):
    """Membersihkan teks dari karakter yang tidak diinginkan."""
    if not text:
        return ""
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'__', '', text)
    text = re.sub(r'_{2,}', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^:\s*', '', text)
    return text.strip()

def extract_section(text, header, stop_patterns):
    """Mengambil konten di bawah header sampai bertemu stop_patterns."""
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

def extract_makna_belgong(text):
    """Khusus untuk Belgong: ambil hanya makna utama."""
    makna_match = re.search(r'Makna\s*:\s*([^.]*\.)', text, re.IGNORECASE | re.DOTALL)
    if makna_match:
        return [clean_text(makna_match.group(1))]
    return []

def extract_contoh_belgong(text):
    """Khusus untuk Belgong: ambil hanya contoh yang benar."""
    contoh_match = re.search(r'Contoh\s*(?:Penggunaan)?\s*:\s*(.*?)(?=Catatan|$)', text, re.IGNORECASE | re.DOTALL)
    if not contoh_match:
        return []
    
    contoh_text = contoh_match.group(1).strip()
    contoh_text = re.sub(r'[•\-*]\s*', '', contoh_text)
    contoh_text = clean_text(contoh_text)
    
    sentences = re.split(r'(?<=[.!?])\s+', contoh_text)
    filtered = []
    for s in sentences:
        if any(kw in s.lower() for kw in ['disebut', 'perhiasan', 'manik', 'kalung']):
            filtered.append(s)
    return filtered[:1] if filtered else []

def extract_contoh_alas(text):
    """Khusus untuk Alas: gabungkan contoh yang terpecah."""
    contoh_content = extract_section(text, "Contoh Kalimat", ["Konteks", "###", "##"])
    if not contoh_content:
        return []
    
    contoh_content = clean_text(contoh_content)
    
    examples = []
    patterns = [
        r'(Alas\s+[^:]+:[^.!?]+[.!?])',
        r'(Alós\s+[^:]+:[^.!?]+[.!?])',
        r'(Nge ara[^.!?]+[.!?])',
        r'(Ialas[^.!?]+[.!?])',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, contoh_content, re.IGNORECASE)
        for m in matches:
            clean = clean_text(m)
            if clean and len(clean) > 10:
                examples.append(clean)
    
    if not examples:
        sentences = re.split(r'(?<=[.!?])\s+', contoh_content)
        for s in sentences:
            if any(kw in s.lower() for kw in ['alas', 'tikar', 'alòs', 'padi', 'serambi']):
                clean = clean_text(s)
                if clean and len(clean) > 10:
                    examples.append(clean)
    
    return examples[:8] if examples else []

def parse_wiki_entry(text, title):
    """Mengurai entri kamus dengan pendekatan berbasis header."""
    if title.lower() == "home":
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
    
    # 4. Makna - khusus untuk Belgong
    if title == "Belgong":
        entry['makna'] = extract_makna_belgong(text)
    else:
        makna_content = extract_section(text, "Makna", ["Contoh", "Catatan", "Konteks", "###"])
        if makna_content:
            if '\n' in makna_content:
                points = [clean_text(p) for p in makna_content.split('\n') if p.strip()]
                entry['makna'] = points if len(points) > 1 else [makna_content]
            else:
                entry['makna'] = [makna_content]
    
    # 5. Contoh - khusus per title
    if title == "Belgong":
        entry['contoh'] = extract_contoh_belgong(text)
    elif title == "Alas":
        entry['contoh'] = extract_contoh_alas(text)
    else:
        contoh_content = extract_section(text, "Contoh Kalimat", ["Konteks", "###", "##"])
        if not contoh_content:
            contoh_content = extract_section(text, "Contoh", ["Konteks", "###", "##"])
        if contoh_content:
            sentences = re.split(r'(?<=[.!?])\s+', contoh_content)
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 5]
            entry['contoh'] = sentences[:5] if sentences else []
    
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

def main():
    print("🔄 Memulai pembersihan semua data...")
    
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
        
        if title.lower() == "home" or not any(kw in text for kw in ["Salabisasi", "Kelas"]):
            skipped.append(title)
            continue
        
        entry = parse_wiki_entry(text, title)
        if entry and (entry.get('makna') or entry.get('kelas_kata')):
            kamus.append(entry)
        else:
            skipped.append(title)
    
    # Simpan hasil
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(kamus, f, indent=2, ensure_ascii=False)
    
    # Simpan daftar yang dilewati
    with open("data/skipped_all.json", 'w', encoding='utf-8') as f:
        json.dump(skipped, f, indent=2, ensure_ascii=False)
    
    # Statistik
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