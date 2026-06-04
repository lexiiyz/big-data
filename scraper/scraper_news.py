import asyncio
import os
import re
from datetime import datetime
from pymongo import MongoClient
from playwright.async_api import async_playwright

KATEGORI_URLS = [
    "https://radarsemarang.jawapos.com/hukum-dan-kriminal",
    "https://radarsemarang.jawapos.com/berita",
]

SEARCH_QUERIES = [
    "Kecelakaan",
    "Banjir",
    "Gempa",
    "Kebakaran",
]

BASE_URL = "https://radarsemarang.jawapos.com"
MAX_PAGES = 3  # Maksimal halaman per sumber


# --- Parser timestamp ---

BULAN_MAP = {
    "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
    "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
    "September": 9, "Oktober": 10, "November": 11, "Desember": 12
}

def parse_radar_timestamp(text: str) -> str | None:
    """
    Parse timestamp format Radar Semarang:
    'Kamis, 28 Mei 2026 | 14:09 WIB' → ISO 8601 string
    """
    try:
        # Buang nama hari dan 'WIB'
        text = re.sub(r'^[A-Za-z]+,\s*', '', text.strip())
        text = text.replace('WIB', '').strip()
        # Format sekarang: '28 Mei 2026 | 14:09'
        parts = text.split('|')
        date_part = parts[0].strip()   # '28 Mei 2026'
        time_part = parts[1].strip() if len(parts) > 1 else "00:00"  # '14:09'

        date_tokens = date_part.split()
        day = int(date_tokens[0])
        month = BULAN_MAP.get(date_tokens[1], 1)
        year = int(date_tokens[2])

        hour, minute = map(int, time_part.split(':'))
        dt = datetime(year, month, day, hour, minute)
        return dt.isoformat()
    except Exception:
        return None


# --- Ambil daftar link dari satu halaman listing ---

async def get_links_from_page(page, url: str) -> list[dict]:
    """
    Ambil semua link artikel beserta timestamp-nya dari satu halaman listing.
    Return: list of {'url': str, 'published_at': str|None}
    """
    print(f"  Crawl halaman: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)  # Tunggu JS render
    except Exception as e:
        print(f"  Gagal load {url}: {e}")
        return []

    try:
        items = await page.evaluate('''() => {
            const results = [];
            // Cari semua link artikel — URL mengandung pola /{kategori}/{id_numerik}/{slug}
            const anchors = document.querySelectorAll('a[href]');
            const seen = new Set();

            anchors.forEach(a => {
                const href = a.href;
                // Filter: URL artikel punya segmen numerik (ID artikel)
                if (!/\\/\\d{10,}\\//.test(href)) return;
                if (seen.has(href)) return;
                seen.add(href);

                // Cari timestamp terdekat di parent element
                let timestamp = null;
                let el = a.closest('article') || a.closest('.item') || a.closest('li') || a.parentElement;
                if (el) {
                    const text = el.innerText || '';
                    // Cari pola 'Hari, DD Bulan YYYY | HH:MM WIB'
                    const match = text.match(/[A-Za-z]+,\\s*\\d{1,2}\\s+\\w+\\s+\\d{4}\\s*\\|\\s*\\d{2}:\\d{2}\\s*WIB/);
                    if (match) timestamp = match[0];
                }

                results.push({ url: href, timestamp_raw: timestamp });
            });

            return results;
        }''')

        result = []
        for item in items:
            result.append({
                "url": item["url"],
                "published_at": parse_radar_timestamp(item["timestamp_raw"]) if item["timestamp_raw"] else None
            })

        print(f"  Ditemukan {len(result)} link.")
        return result

    except Exception as e:
        print(f"  Error ekstrak link: {e}")
        return []


# --- Ambil link dari multi-page (kategori atau search) ---

async def get_all_links(page, base_url: str, max_pages: int = MAX_PAGES) -> list[dict]:
    """Crawl sampai max_pages halaman dari satu sumber."""
    all_links = []
    seen_urls = set()

    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            url = base_url
        else:
            # Radar Semarang pakai query param ?page=N
            separator = "&" if "?" in base_url else "?"
            url = f"{base_url}{separator}page={page_num}"

        links = await get_links_from_page(page, url)
        new_links = [l for l in links if l["url"] not in seen_urls]

        if not new_links:
            print(f"  Tidak ada link baru di halaman {page_num}, berhenti.")
            break

        for l in new_links:
            seen_urls.add(l["url"])
        all_links.extend(new_links)

    return all_links


# --- Scrape isi artikel ---

async def scrape_radar_article(page, url: str, published_at_fallback: str | None = None) -> dict | None:
    """Scrape konten lengkap satu artikel Radar Semarang."""
    print(f"  Scraping artikel: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)
    except Exception as e:
        print(f"  Gagal load artikel {url}: {e}")
        return None

    try:
        result = await page.evaluate('''() => {
            // Judul
            const titleEl = document.querySelector('h1');
            const title = titleEl ? titleEl.innerText.trim() : document.title;

            // Timestamp dari artikel — ambil dari teks di dekat h1
            let published_at_raw = null;
            const allText = document.body.innerText;
            const tsMatch = allText.match(/[A-Za-z]+,\\s*\\d{1,2}\\s+\\w+\\s+\\d{4}\\s*\\|\\s*\\d{2}:\\d{2}\\s*WIB/);
            if (tsMatch) published_at_raw = tsMatch[0];

            // Konten artikel:
            // Radar Semarang tidak punya wrapper class khusus yang konsisten.
            // Strategi: ambil semua <p> dari seluruh body, filter noise.
            const allP = Array.from(document.querySelectorAll('p'));
            
            // Daftar teks yang menandai akhir konten artikel
            const stopMarkers = [
                'Editor :', 'Bagikan:', 'Artikel Terkait', 'Berita Terkini',
                'KONTEN PROMOSI', 'Populer', 'Ikuti Saluran'
            ];
            
            const paragraphs = [];
            let started = false;
            
            for (const p of allP) {
                const text = p.innerText.trim();
                
                // Mulai ambil setelah menemukan teks pembuka khas Radar Semarang
                if (!started && text.startsWith('RADARSEMARANG')) {
                    started = true;
                }
                
                if (!started) continue;
                
                // Berhenti jika ketemu marker akhir artikel
                if (stopMarkers.some(m => text.includes(m))) break;
                
                // Filter noise: terlalu pendek, link "Baca Juga", angka halaman
                if (text.length < 30) continue;
                if (text.includes('Baca Juga:') || text.includes('BACA JUGA')) continue;
                
                paragraphs.push(text);
            }

            // Kategori dari URL path
            const pathParts = window.location.pathname.split('/').filter(Boolean);
            const kategori = pathParts.length > 0 ? pathParts[0] : 'umum';

            return {
                title,
                published_at_raw,
                full_text: paragraphs.join('\\n\\n'),
            };
        }''')

        if not result["full_text"]:
            print(f"  Peringatan: konten kosong untuk {url}")
            return None

        published_at = None
        if result["published_at_raw"]:
            published_at = parse_radar_timestamp(result["published_at_raw"])
        if not published_at:
            published_at = published_at_fallback  # Fallback dari timestamp listing

        return {
            "title": result["title"],
            "url": url,
            "full_text": result["full_text"],
            "source": "Radar Semarang",
            "published_at": published_at,
            "scraped_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        print(f"  Error ekstrak konten: {e}")
        return None


# --- Runner utama ---

async def run_radar_scraper(
    queries: list[str] | None = None,
    kategori_urls: list[str] | None = None,
    max_pages: int = MAX_PAGES,
):
    """
    Scrape Radar Semarang dari search queries dan/atau URL kategori.
    Default: pakai SEARCH_QUERIES dan KATEGORI_URLS yang sudah dikonfigurasi.
    """
    if queries is None:
        queries = SEARCH_QUERIES
    if kategori_urls is None:
        kategori_urls = KATEGORI_URLS

    # Bangun daftar semua sumber URL
    source_urls = []
    for q in queries:
        source_urls.append({
            "url": f"{BASE_URL}/search?q={q}",
            "label": f"search:{q}"
        })
    for k in kategori_urls:
        source_urls.append({
            "url": k,
            "label": f"kategori:{k.split('/')[-1]}"
        })

    async with async_playwright() as p:
        browser = None
        page = None
        try:
            print("Meluncurkan Headless Browser (Radar Semarang)...")
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Koneksi MongoDB
            mongo_uri = os.getenv("MONGO_URI")
            client = MongoClient(mongo_uri)
            collection = client["news_db"]["raw_articles"]

            total_saved = 0

            for source in source_urls:
                print(f"\n[{source['label']}] Mulai crawl...")
                links = await get_all_links(page, source["url"], max_pages=max_pages)

                for link_info in links:
                    url = link_info["url"]

                    # Skip duplikat
                    if collection.count_documents({"url": url}, limit=1) > 0:
                        print(f"  Skip (sudah ada): {url}")
                        continue

                    artikel = await scrape_radar_article(
                        page, url,
                        published_at_fallback=link_info.get("published_at")
                    )

                    if artikel:
                        collection.insert_one(artikel)
                        print(f"  Tersimpan: {artikel['title'][:60]}...")
                        total_saved += 1

                    await asyncio.sleep(1.5)  # Jeda agar tidak diblokir

            print(f"\nSelesai! Total {total_saved} artikel baru tersimpan.")

        except Exception as e:
            print(f"Radar Scraper Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if page: await page.close()
            if browser: await browser.close()
