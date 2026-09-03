# scripts/fix_encoding.py
import json
import os

INPUT_FILE = "web-app/data/kamus.json"
OUTPUT_FILE = "web-app/data/kamus.json"

def fix_encoding():
    print("🔄 Memperbaiki encoding file...")
    
    # Baca dengan encoding yang benar
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Berhasil membaca {len(data)} entri.")
    except UnicodeDecodeError:
        print("⚠️  Gagal membaca dengan UTF-8, mencoba dengan latin-1...")
        with open(INPUT_FILE, 'r', encoding='latin-1') as f:
            data = json.load(f)
        print(f"✅ Berhasil membaca {len(data)} entri dengan latin-1.")
    
    # Simpan ulang dengan encoding UTF-8
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Data disimpan dengan encoding UTF-8.")
    print(f"📊 Jumlah entri: {len(data)}")

if __name__ == "__main__":
    fix_encoding()