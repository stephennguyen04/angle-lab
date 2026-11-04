#!/usr/bin/env node
/**
 * adlib_scrape.cjs: Fallback thu thập ad từ trang Meta Ad Library công khai (khi không có MCP META_ADS).
 *
 * Dùng:
 *   node adlib_scrape.cjs "<URL Ad Library>" <out.json> [--max 300] [--headful]
 *   URL ví dụ: https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&view_all_page_id=<PAGE_ID>&media_type=all
 *
 * Lưu ý:
 *  - Best-effort: Meta đổi giao diện thường xuyên, có thể gặp login wall/captcha → chạy --headful, tự đăng nhập rồi để script cuộn.
 *  - Tôn trọng điều khoản Meta: chỉ dùng cho nghiên cứu, giữ --max ở mức vừa phải.
 *  - Output tương thích scripts/ad_cadence.py.
 */
const fs = require('fs');

let chromium;
try { ({ chromium } = require('playwright')); } catch (e) {
  console.error('Thiếu playwright. Cài: npm i -g playwright && npx playwright install chromium');
  process.exit(2);
}

const args = process.argv.slice(2);
const url = args[0];
const out = args[1] || 'ads_raw.json';
const mi = args.indexOf('--max');
const max = mi >= 0 ? Number(args[mi + 1]) : 300;
const headful = args.includes('--headful');
if (!url) { console.error('Thiếu URL Ad Library'); process.exit(1); }

(async () => {
  const browser = await chromium.launch({ headless: !headful });
  const ctx = await browser.newContext({ locale: 'en-US', viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(6000);

  const totalText = await page.evaluate(() => {
    const m = document.body.innerText.match(/~?\s?([\d,.]+)\s+(results|kết quả)/i);
    return m ? m[0] : null;
  });

  let lastCount = 0, stable = 0;
  for (let i = 0; i < 200; i++) {
    await page.mouse.wheel(0, 4000);
    await page.waitForTimeout(1500);
    const c = await page.evaluate(() => (document.body.innerText.match(/(Library ID|ID thư viện)\s*:?\s*\d+/g) || []).length);
    if (c >= max) break;
    if (c === lastCount) { if (++stable >= 5) break; } else { stable = 0; lastCount = c; }
  }

  const ads = await page.evaluate(() => {
    const idRe = /(Library ID|ID thư viện)\s*:?\s*(\d+)/;
    const leafs = [...document.querySelectorAll('span, div')].filter(el =>
      idRe.test(el.textContent || '') && [...el.children].every(ch => !idRe.test(ch.textContent || '')));
    const seen = new Set();
    const res = [];
    for (const leaf of leafs) {
      // leo lên tới container lớn nhất chỉ chứa đúng 1 Library ID = 1 card
      let card = leaf;
      while (card.parentElement && ((card.parentElement.innerText || '').match(/(Library ID|ID thư viện)/g) || []).length === 1) {
        card = card.parentElement;
      }
      const t = card.innerText || '';
      const id = (t.match(idRe) || [])[2];
      if (!id || seen.has(id)) continue;
      seen.add(id);
      const started = (t.match(/(Started running on|Bắt đầu chạy vào)\s+([^\n·]+)/) || [])[2] || null;
      const range = t.match(/([A-Z][a-z]{2} \d{1,2}, \d{4})\s*-\s*([A-Z][a-z]{2} \d{1,2}, \d{4})/);
      const active = /\bActive\b|Đang hoạt động/.test(t) && !/\bInactive\b|Không hoạt động/.test(t);
      const dup = (t.match(/(\d+)\s+(ads use this creative|quảng cáo dùng)/) || [])[1] || 1;
      const video = card.querySelector('video');
      const links = [...card.querySelectorAll('a[href]')].map(a => a.href);
      let landing = null;
      for (const h of links) {
        try {
          const u = new URL(h);
          if (u.hostname.startsWith('l.facebook.com')) { landing = u.searchParams.get('u'); break; }
          if (!/facebook\.com|instagram\.com|fbcdn/.test(u.hostname)) { landing = h; break; }
        } catch (e) {}
      }
      const lines = t.split('\n').map(s => s.trim()).filter(Boolean);
      const sponsoredIdx = lines.findIndex(l => /^(Sponsored|Được tài trợ)$/.test(l));
      const body = sponsoredIdx >= 0 ? lines.slice(sponsoredIdx + 1, sponsoredIdx + 6).join(' ') : '';
      res.push({
        id,
        start_date: range ? range[1] : started,
        end_date: range ? range[2] : null,
        is_active: active,
        duplicates: Number(dup),
        media_type: video ? 'video' : (card.querySelectorAll('img').length > 3 ? 'carousel' : 'image'),
        video_url: video ? (video.currentSrc || video.src || null) : null,
        landing_url: landing,
        body: body.slice(0, 400),
      });
    }
    return res;
  });

  fs.writeFileSync(out, JSON.stringify({ source_url: url, total_text: totalText, scraped_at: new Date().toISOString(), ads }, null, 2));
  console.log(`Đã lưu ${ads.length} ad → ${out}${totalText ? ` (Ad Library báo: ${totalText})` : ''}`);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
