// --- Konfigurasi ---
const DATA_URL = 'data/kamus.json';

// --- Data Inline (untuk mode tanpa server) ---
window.inlineData = [
  // Tempelkan data kamus di sini jika diperlukan
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
    if (!query || !text) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark class="highlight">$1</mark>');
}

// === FUNGSI BARU: Buat cuplikan teks ===
function getSnippet(text, query, maxLength = 120) {
    if (!query || !text) return text;
    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();
    const index = lowerText.indexOf(lowerQuery);
    if (index === -1) {
        // Jika tidak ditemukan, tampilkan awal teks
        return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
    }
    
    const start = Math.max(0, index - 40);
    const end = Math.min(text.length, index + query.length + 40);
    let snippet = text.slice(start, end);
    
    // Tambahkan elipsis jika dipotong
    if (start > 0) snippet = '...' + snippet;
    if (end < text.length) snippet = snippet + '...';
    
    return highlightText(snippet, query);
}

// --- Render Functions ---
function renderEntry(entry, query = '') {
    const card = document.createElement('div');
    card.className = 'entry-card';

    // === HEADER (sudah pakai highlight) ===
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

    // === MAKNA (dengan snippet + highlight) ===
    if (entry.makna && entry.makna.length > 0) {
        const maknaDiv = document.createElement('div');
        maknaDiv.className = 'entry-makna';
        
        // Tampilkan makna lengkap dengan highlight
        const maknaHTML = entry.makna.map(m => {
            // Jika ada query, tampilkan snippet yang lebih pendek untuk makna panjang
            if (query && m.length > 100) {
                return `<p>${getSnippet(m, query, 150)}</p>`;
            }
            return `<p>${highlightText(m, query)}</p>`;
        }).join('');
        maknaDiv.innerHTML = maknaHTML;
        card.appendChild(maknaDiv);
    }

    // === CONTOH (dengan highlight) ===
    if (entry.contoh && entry.contoh.length > 0) {
        const contohDiv = document.createElement('div');
        contohDiv.className = 'entry-contoh';
        const label = document.createElement('span');
        label.className = 'label';
        label.textContent = '📝 Contoh: ';
        contohDiv.appendChild(label);
        
        const contohHTML = entry.contoh.map(c => 
            `<p>${highlightText(c, query)}</p>`
        ).join('');
        contohDiv.innerHTML += contohHTML;
        card.appendChild(contohDiv);
    }

    // === CATATAN (dengan highlight) ===
    if (entry.catatan) {
        const catatanDiv = document.createElement('div');
        catatanDiv.className = 'entry-catatan';
        catatanDiv.innerHTML = `<span class="label">📌 Catatan:</span> ${highlightText(entry.catatan, query)}`;
        card.appendChild(catatanDiv);
    }

    // === SUMBER ===
    if (entry.sumber) {
        const sumberDiv = document.createElement('div');
        sumberDiv.className = 'entry-sumber';
        sumberDiv.innerHTML = `<span class="label">📖 Sumber:</span> ${highlightText(entry.sumber, query)}`;
        card.appendChild(sumberDiv);
    }

    // === STATUS ===
    const statusSpan = document.createElement('span');
    statusSpan.className = `entry-status ${entry.status || 'sebagian'}`;
    statusSpan.textContent = entry.status || 'sebagian';
    card.appendChild(statusSpan);

    return card;
}

function renderResults(data, query = '') {
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

    // === TAMBAHAN: Tampilkan kata kunci yang dicari ===
    if (query) {
        const infoDiv = document.createElement('div');
        infoDiv.style.cssText = `
            background: #f0f7ff;
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            color: #2c3e50;
            font-size: 0.95rem;
            border-left: 4px solid #3498db;
        `;
        infoDiv.innerHTML = `🔍 Menampilkan <strong>${data.length}</strong> entri yang mengandung kata "<strong>${query}</strong>" di seluruh teks (makna, contoh, catatan, dll.)`;
        entriesContainer.appendChild(infoDiv);
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

    // Filter berdasarkan teks (SUDAH FULL-TEXT SEARCH)
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
    entriesContainer.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #7f8c8d;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 10px;"></i>
            <p>Memuat data kamus...</p>
        </div>
    `;

    try {
        const response = await fetch(DATA_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        kamusData = await response.json();
        console.log(`✅ Data dimuat dari file eksternal: ${kamusData.length} entri`);
    } catch (error) {
        console.warn('⚠️ Gagal memuat dari file eksternal, mencoba data inline...');
        if (window.inlineData && window.inlineData.length > 0) {
            kamusData = window.inlineData;
            console.log(`✅ Data inline berhasil dimuat: ${kamusData.length} entri`);
        } else {
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
console.log('💡 Fitur pencarian mencakup seluruh teks (makna, contoh, catatan, dll.)');