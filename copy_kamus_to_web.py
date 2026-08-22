# D:\korpus-gayo\copy_kamus_to_web.py
import json
import os

# --- Path menggunakan BASE_DIR ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # D:\korpus-gayo
SOURCE = os.path.join(BASE_DIR, "data", "kamus_terstruktur_all.json")
DEST_DIR = os.path.join(BASE_DIR, "web-app", "data")
DEST = os.path.join(DEST_DIR, "kamus.json")

# Buat folder tujuan jika belum ada
os.makedirs(DEST_DIR, exist_ok=True)

# Periksa apakah file sumber ada
if not os.path.exists(SOURCE):
    print(f"❌ File sumber tidak ditemukan: {SOURCE}")
    print("   Pastikan file data/kamus_terstruktur_all.json ada.")
    exit(1)

# Baca data
with open(SOURCE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Simpan ke tujuan
with open(DEST, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Data disalin ke: {DEST}")
print(f"📊 Jumlah entri: {len(data)}")