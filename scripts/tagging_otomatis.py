# scripts/tagging_otomatis.py
import json
import os
import re

# Konfigurasi
INPUT_FILE = "data/kamus_terstruktur_all.json"
OUTPUT_FILE = "data/kamus_terstruktur_with_tags.json"

# Daftar topik dan kata kunci
TOPIC_KEYWORDS = {
    "alam": ["hutan", "gunung", "sungai", "danau", "angin", "hujan", "tanah", "batu", "pohon", "daun", "akar", "bunga", "buah", "air", "api", "matahari", "bulan", "bintang", "awan", "kabut", "embun", "pasir", "lumpur", "rawa", "pantai", "laut"],
    
    "ekologi":  ["ekologis", "ekosistem", "lingkungan", "konservasi", "alami", "alam", "satwa", "flora", "fauna", "habitat", "koridor", "biodiversitas", "pelestarian", "perilaku satwa"],
    
    "pertanian": ["padi", "sawah", "ladang", "tanam", "panen", "cangkul", "bajak", "garu", "bibit", "pupuk", "irigasi", "tumbuhan", "bercocok", "tanam", "kebun", "petani", "gabah", "jerami", "membajak", "menanam", "memotong", "mengetam"],
    
    "perkebunan": ["kopi", "karet", "kelapa", "sawit", "cengkeh", "pala", "lada", "kakao", "teh", "tembakau", "kayu manis", "getah", "buah", "perkebunan", "lahan", "komoditas"],
    
    "peternakan": ["kerbau", "kambing", "ayam", "bebek", "ternak", "kandang", "pakan", "daging", "telur", "susu", "hewan"],
    
    "budaya": ["adat", "upacara", "ritual", "tradisi", "pernikahan", "pengantin", "tarian", "musik", "gendang", "seruling", "nyanyian", "pantun", "cerita", "legenda", "mitos", "budaya", "kekerabatan", "marga", "suku", "kampung", "rumah adat", "pakaian adat", "perhiasan", "senjata tradisional", "gotong royong"],
    
    "sosial": ["keluarga", "kerabat", "saudara", "tetangga", "masyarakat", "desa", "kampung", "solidaritas", "gotong royong", "musyawarah", "hukum adat", "kepala adat", "reje", "sistem sosial", "struktur sosial", "peran", "status", "hierarki", "komunal", "kerja sama"],
    
    "ekonomi": ["perdagangan", "jual", "beli", "barang", "uang", "emas", "perak", "tukar", "pasar", "dagang", "modal", "hutang", "piutang", "upah", "buruh", "pekerjaan", "mata pencaharian"],
    
    "kesehatan": ["obat", "penyakit", "sakit", "luka", "demam", "batuk", "dukun", "tabib", "pijat", "ramuan", "daun obat", "tumbuh-tumbuhan", "kesembuhan", "pasien", "pengobatan", "tradisional", "terapi"],
    
    "peralatan": ["alat", "perkakas", "senjata", "wadah", "anyaman", "tikar", "tembikar", "logam", "kayu", "bambu", "rotan", "pisau", "parang", "kapak", "cangkul", "bajak", "garu", "alat dapur", "alat rumah tangga", "alat musik", "senjata tradisional"],
    
    "bahasa": ["kata", "istilah", "ungkapan", "peribahasa", "metafora", "kiasan", "idiom", "linguistik", "bahasa", "dialek", "pelafalan", "ejaan", "fonetik", "semantik", "leksikon"],
    
    "makanan": ["makan", "minum", "nasi", "lauk", "sayur", "buah", "rempah", "kue", "manisan", "durian", "ketan", "gula", "sirup", "lekat", "enak", "lezat", "penganan", "jajanan"],
    
    "transportasi": ["jalan", "perahu", "rakit", "jembatan", "pelabuhan", "sungai", "laut", "berlayar", "mengarungi", "menyeberang", "berjalan", "berlari", "membawa", "memikul"],
}

# Kata kunci stop (tidak perlu di-tag)
STOP_WORDS = ["dan", "atau", "yang", "ini", "itu", "untuk", "dengan", "dari", "ke", "di", "pada", "sebagai", "adalah", "oleh", "karena", "sehingga", "agar", "supaya", "dapat", "bisa", "mungkin", "tidak", "ada", "saya", "kamu", "dia", "kami", "mereka"]

def clean_text(text):
    """Membersihkan teks untuk analisis kata kunci."""
    if not text:
        return ""
    # Hapus tanda baca
    text = re.sub(r'[^\w\s]', ' ', text)
    # Huruf kecil
    text = text.lower()
    return text

def extract_keywords(text):
    """Mengambil kata-kata penting dari teks."""
    words = clean_text(text).split()
    # Filter stop words dan kata pendek
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return keywords

def assign_topics(entry):
    """Menambahkan topik ke entri berdasarkan kata kunci."""
    topics = set()
    
    # Gabungkan teks dari makna dan contoh
    text_parts = []
    if entry.get("makna"):
        text_parts.extend(entry["makna"])
    if entry.get("contoh"):
        text_parts.extend(entry["contoh"])
    if entry.get("catatan"):
        text_parts.append(entry["catatan"])
    
    full_text = " ".join(text_parts)
    keywords = extract_keywords(full_text)
    
    # Cek setiap topik
    for topic, keyword_list in TOPIC_KEYWORDS.items():
        for keyword in keyword_list:
            if keyword in full_text.lower():
                topics.add(topic)
                break
    
    return list(topics)

def main():
    print("🏷️  Memulai penambahan tag otomatis...")
    
    # Baca file
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Ditemukan {len(data)} entri.")
    
    # Proses setiap entri
    tagged_count = 0
    for entry in data:
        topics = assign_topics(entry)
        if topics:
            entry["topik"] = topics
            tagged_count += 1
        else:
            entry["topik"] = []
    
    # Simpan hasil
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Selesai! {tagged_count} entri berhasil diberi tag.")
    print(f"💾 Data disimpan ke: {OUTPUT_FILE}")
    
    # Statistik topik
    topic_stats = {}
    for entry in data:
        for topic in entry.get("topik", []):
            topic_stats[topic] = topic_stats.get(topic, 0) + 1
    
    print("\n📊 Statistik Topik:")
    for topic, count in sorted(topic_stats.items(), key=lambda x: -x[1]):
        print(f"   - {topic}: {count} entri")

if __name__ == "__main__":
    main()