// --- Konfigurasi ---
const DATA_URL = 'data/kamus.json';

// --- Data Inline (untuk mode tanpa server) ---
// Data ini akan digunakan jika fetch ke file eksternal gagal.
// Tempelkan isi file data/kamus_terstruktur_all.json di sini.
window.inlineData = [
  //  ========== TEMPELKAN DATA KAMUS DI SINI ==========
  // Contoh:
  // {
  //   "kata": "Belgong",
  //   "ejaan_alternatif": "bĕlgong",
  //   "suku_kata": "bĕ·le·gong / bĕl·gong",
  //   "kelas_kata": "nomina",
  //   "makna": ["Kalung, biasanya terbuat dari manik-manik..."],
  //   "contoh": ["Disebut secara definisional..."],
  //   "catatan": "Sebagai barang impor...",
  //   "sumber": "Hazeu (1907)",
  //   "status": "lengkap"
  // },
  // ===================================================
];

// --- State ---
let kamusData = [];
let filteredData = [];

// --- DOM References ---
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const filterKelas = document.getElementById('filterKelas');
const filterStatus = document.getElementById('filterStatus');
const resultCount = document.getElementById('resultCount');
const entriesContainer = document.getElementById('entriesContainer');
const welcomeSection = document.getElementById('welcomeSection');
const resultsSection = document.getElementById('resultsSection');
const totalEntries = document.getElementById('totalEntries');

// --- Utility Functions ---
function normalizeText(text) {
    return text.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function highlightText(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

// --- Render Functions ---
function renderEntry(entry, query = '') {
    const card = document.createElement('div');
    card.className = 'entry-card';

    // Header
    const header = document.createElement('div');
    header.className = 'entry-header';
    
    let kataHtml = `<span class="kata">${highlightText(entry.kata, query)}</span>`;
    if (entry.ejaan_alternatif) {
        kataHtml += ` <span class="ejaan-alternatif">(${highlightText(entry.ejaan_alternatif, query)})</span>`;
    }
    if (entry.suku_kata) {
        kataHtml += ` <span class="suku-kata">${highlightText(entry.suku_kata, query)}</span>`;
    }
    if (entry.kelas_kata) {
        kataHtml += ` <span class="kelas-kata">${highlightText(entry.kelas_kata, query)}</span>`;
    }
    header.innerHTML = kataHtml;
    card.appendChild(header);

    // Makna
    if (entry.makna && entry.makna.length > 0) {
        const maknaDiv = document.createElement('div');
        maknaDiv.className = 'entry-makna';
        maknaDiv.innerHTML = entry.makna.map(m => `<p>${highlightText(m, query)}</p>`).join('');
        card.appendChild(maknaDiv);
    }

    // Contoh
    if (entry.contoh && entry.contoh.length > 0) {
        const contohDiv = document.createElement('div');
        contohDiv.className = 'entry-contoh';
        const label = document.createElement('span');
        label.className = 'label';
        label.textContent = 'Contoh: ';
        contohDiv.appendChild(label);
        contohDiv.innerHTML += entry.contoh.map(c => `<p>${highlightText(c, query)}</p>`).join('');
        card.appendChild(contohDiv);
    }

    // Catatan
    if (entry.catatan) {
        const catatanDiv = document.createElement('div');
        catatanDiv.className = 'entry-catatan';
        catatanDiv.innerHTML = `<span class="label">Catatan:</span> ${highlightText(entry.catatan, query)}`;
        card.appendChild(catatanDiv);
    }

    // Sumber
    if (entry.sumber) {
        const sumberDiv = document.createElement('div');
        sumberDiv.className = 'entry-sumber';
        sumberDiv.innerHTML = `<span class="label">Sumber:</span> ${highlightText(entry.sumber, query)}`;
        card.appendChild(sumberDiv);
    }

    // Status
    const statusSpan = document.createElement('span');
    statusSpan.className = `entry-status ${entry.status || 'sebagian'}`;
    statusSpan.textContent = entry.status || 'sebagian';
    card.appendChild(statusSpan);

    return card;
}

function renderResults(data, query = '') {
    // Kosongkan container
    entriesContainer.innerHTML = '';

    if (data.length === 0) {
        entriesContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #7f8c8d;">
                <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 10px;"></i>
                <p>Tidak ditemukan entri yang sesuai.</p>
                <p style="font-size: 0.9rem;">Coba gunakan kata kunci lain atau hapus filter.</p>
            </div>
        `;
        return;
    }

    data.forEach(entry => {
        const card = renderEntry(entry, query);
        entriesContainer.appendChild(card);
    });
}

// --- Filter Functions ---
function applyFilters() {
    const query = searchInput.value.trim();
    const kelas = filterKelas.value;
    const status = filterStatus.value;

    let results = kamusData;

    // Filter berdasarkan teks
    if (query) {
        const searchTerm = query.toLowerCase();
        results = results.filter(entry => {
            const searchFields = [
                entry.kata,
                entry.ejaan_alternatif,
                entry.suku_kata,
                entry.kelas_kata,
                ...(entry.makna || []),
                ...(entry.contoh || []),
                entry.catatan,
                entry.sumber
            ].filter(Boolean);
            return searchFields.some(field => field.toLowerCase().includes(searchTerm));
        });
    }

    // Filter berdasarkan kelas kata
    if (kelas !== 'all') {
        results = results.filter(entry => 
            entry.kelas_kata && entry.kelas_kata.toLowerCase().includes(kelas.toLowerCase())
        );
    }

    // Filter berdasarkan status
    if (status !== 'all') {
        results = results.filter(entry => entry.status === status);
    }

    filteredData = results;
    resultCount.textContent = `${results.length} entri ditemukan`;
    renderResults(results, query);
}

// --- Load Data ---
async function loadData() {
    // Tampilkan loading
    entriesContainer.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #7f8c8d;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 10px;"></i>
            <p>Memuat data kamus...</p>
        </div>
    `;

    try {
        // 1. Coba ambil dari file eksternal
        const response = await fetch(DATA_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        kamusData = await response.json();
        console.log(`✅ Data dimuat dari file eksternal: ${kamusData.length} entri`);
    } catch (error) {
        console.warn('⚠️ Gagal memuat dari file eksternal, mencoba data inline...');
        // 2. Jika gagal, gunakan data inline
        if (window.inlineData && window.inlineData.length > 0) {
            kamusData = window.inlineData;
            console.log(`✅ Data inline berhasil dimuat: ${kamusData.length} entri`);
        } else {
            // 3. Jika inlineData kosong, tampilkan error
            console.error('❌ Tidak ada data inline yang tersedia.');
            entriesContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #e74c3c;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>Data kamus tidak tersedia. Pastikan file <code>data/kamus.json</code> ada atau data inline telah diisi.</p>
                    <p style="font-size: 0.9rem; color: #95a5a6;">Error: ${error.message}</p>
                </div>
            `;
            return;
        }
    }

    // Update UI
    totalEntries.textContent = kamusData.length;
    filteredData = kamusData;
    applyFilters();
}

// --- Event Listeners ---
searchInput.addEventListener('input', applyFilters);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        applyFilters();
    }
});
searchButton.addEventListener('click', applyFilters);
filterKelas.addEventListener('change', applyFilters);
filterStatus.addEventListener('change', applyFilters);

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    loadData();
});

// Console info
console.log('🔍 Kamus Bahasa Gayo loaded.');
console.log('📖 Sumber: Hazeu (1907)');
console.log('💡 Gunakan kotak pencarian untuk mencari kata.');