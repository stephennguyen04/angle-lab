#!/usr/bin/env node
/**
 * capture_page.cjs: Đi theo link ad như khách thật (mobile), ghi lại funnel & dựng hình trang.
 *
 * Dùng: node capture_page.cjs "<url>" <out_dir> [--follow-cta]
 *   --follow-cta : nếu trang đầu là advertorial/listicle, tự click CTA chính để chụp tiếp trang sản phẩm (bước 2 funnel)
 *
 * Output trong out_dir:
 *   step1_summary.md  : ĐỌC FILE NÀY TRƯỚC (gọn): loại trang, heading, CTA, giá, dấu hiệu, app, 250 chữ đầu
 *   step1_fold.png    : màn hình đầu tiên (above the fold) · step1_bundle.png: khu bundle/offer (nếu tìm thấy)
 *   step1.png / step1.json / step1.txt : toàn trang, chỉ mở khi cần  (và step2.* nếu follow CTA)
 *   funnel.json: chuỗi redirect + page_type từng bước
 */
const fs = require('fs');
const path = require('path');

let chromium, devices;
try { ({ chromium, devices } = require('playwright')); } catch (e) {
  console.error('Thiếu playwright. Cài: npm i -g playwright && npx playwright install chromium');
  process.exit(2);
}

const [url, outDir = 'page_capture'] = process.argv.slice(2);
const followCta = process.argv.includes('--follow-cta');
if (!url) { console.error('Thiếu URL'); process.exit(1); }
fs.mkdirSync(outDir, { recursive: true });

async function analyze(page) {
  return page.evaluate(() => {
    const txt = document.body.innerText || '';
    const words = txt.split(/\s+/).filter(Boolean).length;
    const q = s => [...document.querySelectorAll(s)];
    const heads = q('h1,h2,h3').map(h => ({ tag: h.tagName, text: h.innerText.trim().slice(0, 160) })).filter(h => h.text).slice(0, 60);
    const ctaRe = /(add to cart|buy now|shop now|order now|get yours|claim|check availability|try it|thêm vào giỏ|mua ngay|đặt hàng|nhận ưu đãi|xem sản phẩm)/i;
    const ctas = q('a,button').map(el => ({ text: (el.innerText || el.value || '').trim().slice(0, 80), href: el.href || null }))
      .filter(c => c.text && ctaRe.test(c.text));
    const ctaHrefs = {};
    ctas.forEach(c => { if (c.href) ctaHrefs[c.href.split('?')[0]] = (ctaHrefs[c.href.split('?')[0]] || 0) + 1; });
    const prices = [...new Set((txt.match(/(?:[$€£₫]|USD|VND|AUD)\s?\d[\d.,]*|\d[\d.,]*\s?(?:₫|đ|VND|USD)/g) || []))].slice(0, 30);
    const has = re => re.test(txt);
    const markers = {
      add_to_cart_form: !!document.querySelector('form[action*="/cart/add"], [name="add"], button[name="add"]'),
      byline_or_date: has(/\b(by|written by|bởi)\s+[A-Z][a-z]+|\b(updated|published|cập nhật)\b/i),
      advertorial_label: has(/advertorial|sponsored|paid content|quảng cáo/i),
      numbered_reasons: heads.filter(h => /^(#?\d+[.)]|reason|lý do)/i.test(h.text)).length,
      fake_comments: has(/(like · reply|thích · phản hồi|\d+\s?(m|h|d)\b.*reply)/i),
      quiz: has(/(take the quiz|start quiz|câu hỏi \d|question \d of)/i),
      countdown: has(/(ends in|hết hạn sau|\d{2}\s?:\s?\d{2}\s?:\s?\d{2})/i),
      bundle_offer: has(/(buy \d+ get|mua \d+ tặng|\d+\s?(pack|pcs|bottles|hộp|chai)|bundle|most popular|best value|phổ biến nhất|tiết kiệm nhất)/i),
      guarantee: has(/(money.back|guarantee|risk.free|hoàn tiền|đổi trả|bảo hành)/i),
      reviews: has(/(\d[\d,.]*\s?(reviews|đánh giá))|judge\.me|loox|okendo|yotpo/i),
      free_shipping: has(/(free shipping|miễn phí vận chuyển|freeship)/i),
      bnpl: has(/(klarna|afterpay|shop pay installments|zip pay|trả góp)/i),
      video_count: document.querySelectorAll('video, iframe[src*="youtube"], iframe[src*="vimeo"], iframe[src*="wistia"]').length,
    };
    let page_type = 'khác';
    if (markers.quiz) page_type = 'quiz';
    else if (markers.add_to_cart_form || /\/products\//.test(location.pathname)) page_type = 'PDP';
    else if (markers.numbered_reasons >= 3) page_type = 'listicle';
    else if (words > 1000 && (markers.byline_or_date || markers.advertorial_label || markers.fake_comments)) page_type = 'advertorial';
    else if (markers.video_count >= 1 && words < 400) page_type = 'VSL';
    else if (/\/collections\//.test(location.pathname)) page_type = 'collection';
    else if (location.pathname === '/' ) page_type = 'homepage';
    const apps = [];
    const html = document.documentElement.innerHTML;
    [['kaching', /kaching/i], ['bundler/quantity-breaks', /bundler|quantity.?break|volume.?discount/i], ['judge.me', /judge\.me/i],
     ['loox', /loox/i], ['okendo', /okendo/i], ['yotpo', /yotpo/i], ['reconvert', /reconvert/i], ['zipify/oneclick upsell', /zipify|ocu/i],
     ['aftersell', /aftersell/i], ['klaviyo', /klaviyo/i], ['gempages', /gempages/i], ['pagefly', /pagefly/i], ['replo', /replo/i],
     ['shogun', /shogun/i], ['funnelish', /funnelish/i], ['clickfunnels', /clickfunnels/i], ['shopify', /cdn\.shopify\.com/i]]
      .forEach(([n, re]) => { if (re.test(html)) apps.push(n); });
    return { url: location.href, title: document.title, words, headings: heads, ctas: ctas.slice(0, 25), cta_targets: ctaHrefs,
             prices, markers, page_type, apps, text: txt.slice(0, 60000) };
  });
}

function summaryMd(step, info) {
  // Bản tóm tắt gọn (~1–2K token) để AI đọc trước, thay vì text đầy đủ (tới 60K ký tự) + ảnh toàn trang
  const on = Object.entries(info.markers).filter(([k, v]) => v && k !== 'video_count').map(([k]) => k);
  const words = info.text.split(/\s+/).filter(Boolean);
  return [
    `# ${step}: ${info.page_type} · ${info.words} chữ`,
    `URL: ${info.url}`, `Title: ${info.title}`,
    `Dấu hiệu: ${on.join(', ') || '—'} · video: ${info.markers.video_count}`, `App: ${info.apps.join(', ') || '—'}`,
    `Giá thấy trên trang: ${info.prices.slice(0, 12).join(' · ') || '—'}`,
    '', '## Heading (theo thứ tự)', ...info.headings.slice(0, 30).map(h => `- ${h.tag}: ${h.text}`),
    '', '## CTA', ...info.ctas.slice(0, 10).map(c => `- ${c.text}${c.href ? ' → ' + c.href.split('?')[0] : ''}`),
    '', '## 250 chữ đầu', words.slice(0, 250).join(' '),
    '', `_Đầy đủ: ${step}.txt (text) · ${step}.png (toàn trang) · ${step}_fold.png (màn hình đầu) · ${step}_bundle.png (khu bundle, nếu có)_`,
  ].join('\n');
}

async function capture(page, step) {
  await page.screenshot({ path: path.join(outDir, `${step}_fold.png`) }).catch(() => {});   // màn hình đầu tiên
  for (let i = 0; i < 25; i++) { await page.mouse.wheel(0, 1200); await page.waitForTimeout(250); }
  await page.waitForTimeout(1200);
  const info = await analyze(page);
  await page.screenshot({ path: path.join(outDir, `${step}.png`), fullPage: true }).catch(() => {});
  // Ảnh riêng khu bundle/offer: tìm phần tử nhỏ nhất chứa chữ kiểu "Buy 2", "2 Pack", "Mua 2", "Most popular"
  try {
    const box = await page.evaluate(() => {
      const re = /(buy\s*\d|\d\s*(pack|pcs|bottles?|hộp|chai|bộ)\b|mua\s*\d|most popular|best value|phổ biến nhất|bundle)/i;
      let best = null;
      for (const el of document.querySelectorAll('div,section,form,ul,fieldset')) {
        const t = el.innerText || '';
        if (!re.test(t)) continue;
        const r = el.getBoundingClientRect();
        if (r.height < 80 || r.width < 200 || r.height > 1600) continue;
        if (!best || r.height * r.width < best.area) best = { x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height, area: r.width * r.height };
      }
      return best;
    });
    if (box) await page.screenshot({ path: path.join(outDir, `${step}_bundle.png`), fullPage: true,
      clip: { x: Math.max(0, box.x - 8), y: Math.max(0, box.y - 40), width: box.w + 16, height: Math.min(box.h + 120, 1800) } });
  } catch (e) {}
  fs.writeFileSync(path.join(outDir, `${step}.txt`), info.text);
  fs.writeFileSync(path.join(outDir, `${step}_summary.md`), summaryMd(step, info));
  delete info.text;
  fs.writeFileSync(path.join(outDir, `${step}.json`), JSON.stringify(info, null, 2));
  return info;
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 13'] });
  const page = await ctx.newPage();
  const chain = [];
  page.on('response', r => {
    if (r.request().isNavigationRequest() && r.request().frame() === page.mainFrame()) chain.push({ status: r.status(), url: r.url() });
  });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(3000);
  const steps = [await capture(page, 'step1')];

  if (followCta && steps[0].page_type !== 'PDP') {
    const targets = Object.entries(steps[0].cta_targets).sort((a, b) => b[1] - a[1]);
    if (targets.length) {
      await page.goto(targets[0][0], { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.waitForTimeout(3000);
      steps.push(await capture(page, 'step2'));
    }
  }
  const funnel = {
    entry_url: url,
    redirect_chain: chain,
    steps: steps.map((s, i) => ({ step: i + 1, url: s.url, page_type: s.page_type, words: s.words, apps: s.apps })),
    funnel_shape: steps.map(s => s.page_type).join(' → '),
  };
  fs.writeFileSync(path.join(outDir, 'funnel.json'), JSON.stringify(funnel, null, 2));
  console.log(`Funnel: ${funnel.funnel_shape}  (lưu ở ${outDir}/)`);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
