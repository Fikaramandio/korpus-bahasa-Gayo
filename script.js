// --- Konfigurasi ---
const DATA_URL = 'data/kamus.json';

// --- Data Inline (untuk mode tanpa server) ---
window.inlineData = [];

// --- State ---
let kamusData = [];
let filteredData = [];

// --- DOM References ---
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const filterKelas = document.getElementById('filterKelas');
const filterStatus = document.getElementById('filterStatus');
const filterTopik = document.getElementById('filterTopik');
const resultCount = document.getElementById('resultCount');
const entriesContainer = document.getElementById('entriesContainer');
const welcomeSection = document.getElementById('welcomeSection');
const resultsSection = document.getElementById('resultsSection');
const totalEntries = document.getElementById('totalEntries');

// --- Utility Functions ---
function highlightText(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

// --- Render Functions ---
function renderEntry(entry, query = '') {
    const card = document.createElement('div');
    card.className = 'entry-card';

    // --- Header dengan link ke GitHub Wiki ---
    const header = document.createElement('div');
    header.className = 'entry-header';

    // Buat link ke GitHub Wiki
    const wikiLink = `https://github.com/Fikaramandio/korpus-bahasa-Gayo/wiki/${encodeURIComponent(entry.kata)}`;

    let kataHtml = `<span class="kata"><a href="${wikiLink}" target="_blank" title="Buka di GitHub Wiki" style="color: #1a73e8; text-decoration: none; font-weight: bold;">${highlightText(entry.kata, query)}</a></span>`;
    if (entry.ejaan_alternatif) {
        kataHtml += ` <span class="ejaan-alternatif">(${highlightText(entry.ejaan_alternatif, query)})</span>`;
    }
    if (entry.suku_kata) {
        kataHtml += ` <span class="suku-kata">${highlightText(entry.suku_kata, query)}</span>`;
    }
    if (entry.kelas_kata) {
        kataHtml += ` <span class="kelas-kata">${highlightText(entry.kelas_kata, query)}</span>`;
    }
    // Tambahkan ikon link
    kataHtml += ` <a href="${wikiLink}" target="_blank" title="Buka di GitHub Wiki" style="font-size: 0.9rem; color: #1a73e8; text-decoration: none; margin-left: 5px; background: #e8f0fe; padding: 2px 6px; border-radius: 4px;">🔗 Wiki</a>`;
    header.innerHTML = kataHtml;
    card.appendChild(header);

    // --- Makna ---
    if (entry.makna && entry.makna.length > 0) {
        const maknaDiv = document.createElement('div');
        maknaDiv.className = 'entry-makna';
        maknaDiv.innerHTML = entry.makna.map(m => `<p>${highlightText(m, query)}</p>`).join('');
        card.appendChild(maknaDiv);
    }

    // --- Contoh ---
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

    // --- Catatan ---
    if (entry.catatan) {
        const catatanDiv = document.createElement('div');
        catatanDiv.className = 'entry-catatan';
        catatanDiv.innerHTML = `<span class="label">Catatan:</span> ${highlightText(entry.catatan, query)}`;
        card.appendChild(catatanDiv);
    }

    // --- Topik / Tag ---
    if (entry.topik && entry.topik.length > 0) {
        const topikDiv = document.createElement('div');
        topikDiv.className = 'entry-topik';
        topikDiv.innerHTML = entry.topik.map(t => `<span class="tag">${t}</span>`).join(' ');
        card.appendChild(topikDiv);
    }

    return card;
}

function renderResults(data, query = '') {
    entriesContainer.innerHTML = '';

    if (welcomeSection) welcomeSection.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'block';

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
    const topik = filterTopik.value;

    let results = kamusData;

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
                ...(entry.topik || [])
            ].filter(Boolean);
            return searchFields.some(field => field.toLowerCase().includes(searchTerm));
        });
    }

    if (topik !== 'all') {
        results = results.filter(entry => 
            entry.topik && entry.topik.includes(topik)
        );
    }

    if (kelas !== 'all') {
        results = results.filter(entry => 
            entry.kelas_kata && entry.kelas_kata.toLowerCase().includes(kelas.toLowerCase())
        );
    }

    if (status !== 'all') {
        results = results.filter(entry => entry.status === status);
    }

    filteredData = results;
    if (resultCount) {
        resultCount.textContent = `${results.length} entri ditemukan`;
    }
    renderResults(results, query);
}

// --- Load Data ---
async function loadData() {
    if (entriesContainer) {
        entriesContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #7f8c8d;">
                <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 10px;"></i>
                <p>Memuat data kamus...</p>
            </div>
        `;
    }

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
            if (entriesContainer) {
                entriesContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #e74c3c;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <p>Data kamus tidak tersedia. Pastikan file <code>data/kamus.json</code> ada.</p>
                    </div>
                `;
            }
            return;
        }
    }

    if (totalEntries) {
        totalEntries.textContent = kamusData.length;
    }
    filteredData = kamusData;
    applyFilters();
}

// --- Event Listeners ---
if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            applyFilters();
        }
    });
}
if (searchButton) {
    searchButton.addEventListener('click', applyFilters);
}
if (filterKelas) {
    filterKelas.addEventListener('change', applyFilters);
}
if (filterStatus) {
    filterStatus.addEventListener('change', applyFilters);
}
if (filterTopik) {
    filterTopik.addEventListener('change', applyFilters);
}

// --- Random Entry Feature ---
function showRandomEntry() {
    if (kamusData.length === 0) {
        alert('Data kamus belum dimuat. Silakan tunggu sebentar.');
        return;
    }
    const randomIndex = Math.floor(Math.random() * kamusData.length);
    const entry = kamusData[randomIndex];
    
    searchInput.value = '';
    filterKelas.value = 'all';
    filterStatus.value = 'all';
    filterTopik.value = 'all';
    
    resultCount.textContent = '1 entri acak';
    renderResults([entry], '');
}

// --- Event Listener untuk Random Button ---
const randomButton = document.getElementById('randomButton');
if (randomButton) {
    randomButton.addEventListener('click', showRandomEntry);
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    loadData();
});

console.log('🔍 Kamus Bahasa Gayo loaded.');
console.log('📖 Sumber: Hazeu (1907)');