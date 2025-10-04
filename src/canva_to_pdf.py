import sys
from playwright.sync_api import sync_playwright
from PyPDF2 import PdfMerger
import os

if len(sys.argv) < 2:
    print("Usage: python canva_to_pdf.py <canva-view-url> [out.pdf]")
    sys.exit(1)

base_url = sys.argv[1].split("#")[0]  # strip any #1
out = sys.argv[2] if len(sys.argv) > 2 else "out.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    pdfs = []
    for i in range(1, 14):  # Pages 1 to 13
        url = f"{base_url}#{i}"
        print(f"Rendering page {i}/13 -> {url}")

        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.set_default_navigation_timeout(60000)  # 60s
        
        try:
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
            except Exception as e:
                print(f"Warning: first goto failed for page {i}: {e}. Retrying once...")
                page.goto(url, wait_until="networkidle", timeout=90000)
            
            # Wait for design to load
            try:
                page.wait_for_selector('div[class*="V5ZeDQ"], [aria-label="Design slider"], canvas', timeout=8000)
            except Exception:
                page.wait_for_timeout(2000)

            # Hide UI and isolate design (using raw string to fix SyntaxWarning)
            dims = page.evaluate(r"""
            () => {
              const hideAll = (sel) => Array.from(document.querySelectorAll(sel)).forEach(n => { try { n.style.setProperty('display','none','important'); } catch(e){} });

              // Target known header/footer wrappers and controls
              hideAll('div[class^="V5ZeDQ"]');
              hideAll('div[class*="V5ZeDQ"]');
              hideAll('div[aria-label="Design slider"]');
              hideAll('div.kp6g_Q');
              hideAll('div._8K36tA');
              hideAll('div._7_nW9A');

              // Hide obvious text UI (Canva, Share, page x of y)
              Array.from(document.querySelectorAll('a, button, span, div')).forEach(el => {
                try {
                  const txt = (el.innerText || '').trim().toLowerCase();
                  if (!txt) return;
                  if (txt.includes('canva') || txt.includes('share') || /page \d+ of \d+/i.test(txt)) {
                    el.style.setProperty('display','none','important');
                  }
                } catch(e) {}
              });

              // Heuristic: find the largest visible, non-fixed element inside body (likely the design canvas)
              const isVisible = (el) => {
                try {
                  const st = window.getComputedStyle(el);
                  if (st.display === 'none' || st.visibility === 'hidden' || parseFloat(st.opacity) === 0) return false;
                  const r = el.getBoundingClientRect();
                  if (r.width === 0 || r.height === 0) return false;
                  return true;
                } catch(e){ return false; }
              };

              let best = null;
              let bestArea = 0;
              const all = Array.from(document.body.querySelectorAll('*'));
              for (const el of all) {
                if (!isVisible(el)) continue;
                try {
                  const st = window.getComputedStyle(el);
                  if (st.position === 'fixed' || st.position === 'sticky') continue;
                  const r = el.getBoundingClientRect();
                  if (r.width < 50 || r.height < 50) continue;
                  const area = r.width * r.height;
                  if (area > bestArea) { bestArea = area; best = el; }
                } catch(e) {}
              }

              if (best) {
                // Hide all top-level body children except the ancestors of best so the document contains only the design
                const ancestors = new Set();
                let p = best;
                while (p) { ancestors.add(p); p = p.parentElement; }
                Array.from(document.body.children).forEach(ch => {
                  if (!ancestors.has(ch)) {
                    try { ch.style.setProperty('display','none','important'); } catch(e) {}
                  }
                });

                // Ensure best is cleanly positioned
                try {
                  best.style.setProperty('margin', '0', 'important');
                  best.style.setProperty('position', 'relative', 'important');
                  best.style.setProperty('top', '0', 'important');
                  best.style.setProperty('left', '0', 'important');
                } catch(e) {}
              }

              // Return the page dimensions after isolation; fallback to document size if something goes wrong
              return { w: document.documentElement.scrollWidth || document.body.scrollWidth || 1920, h: document.documentElement.scrollHeight || document.body.scrollHeight || 1080 };
            }
            """)

            page.wait_for_timeout(300)

            full_width = dims.get('w') if isinstance(dims, dict) else dims['w']
            full_height = dims.get('h') if isinstance(dims, dict) else dims['h']

            tmp_pdf = f"tmp_page_{i}.pdf"
            page.pdf(
                path=tmp_pdf,
                width=f"{full_width}px",
                height=f"{full_height}px",
                print_background=True
            )
            pdfs.append(tmp_pdf)
            
        except Exception as e:
            print(f"Error rendering page {i} ({url}): {e}")
        finally:
            try:
                page.close()
            except:
                pass

    browser.close()

# Merge all page PDFs into one
merger = PdfMerger()
for pdf in pdfs:
    merger.append(pdf)
merger.write(out)
merger.close()

# Cleanup temp PDFs
for pdf in pdfs:
    os.remove(pdf)

print(f"Saved PDF to {out}")
