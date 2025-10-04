import sys
from playwright.sync_api import sync_playwright
from PyPDF2 import PdfMerger
import os

if len(sys.argv) < 2:
    print("Usage: python canva_to_pdf.py <canva-view-url> [out.pdf] [--debug]")
    sys.exit(1)

base_url = sys.argv[1].split("#")[0]  # strip any #1
out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "out.pdf"
debug = '--debug' in sys.argv or '--no-headless' in sys.argv

with sync_playwright() as p:
    browser = p.chromium.launch(headless=not debug)
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

            # Find and isolate design using scoring heuristics
            dims = page.evaluate(r"""
            () => {
              const isVisible = (el) => {
                try {
                  const st = window.getComputedStyle(el);
                  if (st.display === 'none' || st.visibility === 'hidden' || parseFloat(st.opacity) === 0) return false;
                  const r = el.getBoundingClientRect();
                  return r.width > 0 && r.height > 0;
                } catch(e) { return false; }
              };

              const scoreElement = (el) => {
                try {
                  const r = el.getBoundingClientRect();
                  const st = window.getComputedStyle(el);
                  
                  if (!isVisible(el) || st.position === 'fixed' || st.position === 'sticky') return -1;
                  if (r.width * r.height < 2000) return -1;
                  
                  let score = r.width * r.height; // Base score: area
                  
                  // Bonus for image content
                  const images = el.querySelectorAll('img, svg, canvas');
                  score += images.length * 10000;
                  
                  // Penalty for UI patterns
                  const className = el.className || '';
                  if (className.includes('V5ZeDQ') || className.includes('_8K36tA') || className.includes('_7_nW9A')) {
                    score *= 0.1;
                  }
                  
                  // Penalty for control elements
                  const controls = el.querySelectorAll('button[aria-label*="Share"], button[aria-label*="Previous"], button[aria-label*="Next"], a[href*="canva.com"]');
                  if (controls.length > 0) score *= 0.1;
                  
                  // Bonus for center position
                  const centerX = r.left + r.width / 2;
                  const centerY = r.top + r.height / 2;
                  const distFromCenter = Math.sqrt(Math.pow(centerX - window.innerWidth/2, 2) + Math.pow(centerY - window.innerHeight/2, 2));
                  score *= Math.max(0.5, 1 - distFromCenter / (window.innerWidth + window.innerHeight));
                  
                  return score;
                } catch(e) { return -1; }
              };

              // Find best element
              let best = null;
              let bestScore = -1;
              const candidates = Array.from(document.body.querySelectorAll('*'));
              
              for (const el of candidates) {
                const score = scoreElement(el);
                if (score > bestScore) {
                  bestScore = score;
                  best = el;
                }
              }

              let debug = { tag: 'none', score: 0, rect: {}, hasImages: false };
              
              if (best) {
                const r = best.getBoundingClientRect();
                const images = best.querySelectorAll('img, svg, canvas');
                debug = {
                  tag: best.tagName,
                  id: best.id || '',
                  classes: (best.className || '').split(' ').slice(0, 3).join(' '),
                  score: bestScore,
                  rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
                  hasImages: images.length > 0
                };
                
                // Scroll into view and wait for images
                best.scrollIntoView({ behavior: 'instant', block: 'start' });
                
                // Clone best element into clean document
                const clone = best.cloneNode(true);
                document.body.innerHTML = '';
                document.body.appendChild(clone);
                
                // Reset positioning
                clone.style.margin = '0';
                clone.style.position = 'relative';
                clone.style.top = '0';
                clone.style.left = '0';
                
                // Wait for images in clone to load
                const cloneImages = clone.querySelectorAll('img');
                return new Promise(resolve => {
                  let loaded = 0;
                  const total = cloneImages.length;
                  
                  if (total === 0) {
                    const finalR = clone.getBoundingClientRect();
                    resolve({ 
                      w: Math.min(Math.max(finalR.width, 800), 20000), 
                      h: Math.min(Math.max(finalR.height, 600), 20000), 
                      debug 
                    });
                    return;
                  }
                  
                  const checkComplete = () => {
                    loaded++;
                    if (loaded >= total) {
                      setTimeout(() => {
                        const finalR = clone.getBoundingClientRect();
                        resolve({ 
                          w: Math.min(Math.max(finalR.width, 800), 20000), 
                          h: Math.min(Math.max(finalR.height, 600), 20000), 
                          debug 
                        });
                      }, 100);
                    }
                  };
                  
                  cloneImages.forEach(img => {
                    if (img.complete) checkComplete();
                    else {
                      img.onload = checkComplete;
                      img.onerror = checkComplete;
                    }
                  });
                  
                  // Fallback timeout
                  setTimeout(() => {
                    const finalR = clone.getBoundingClientRect();
                    resolve({ 
                      w: Math.min(Math.max(finalR.width, 800), 20000), 
                      h: Math.min(Math.max(finalR.height, 600), 20000), 
                      debug 
                    });
                  }, 3000);
                });
              }
              
              return { w: 1920, h: 1080, debug };
            }
            """)

            full_width = dims['w']
            full_height = dims['h']
            
            if debug:
                d = dims['debug']
                print(f"  Debug: {d['tag']} id='{d['id']}' classes='{d['classes']}' rect={d['rect']} images={d['hasImages']} score={d['score']:.0f}")

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
            # Try frame fallback if main page failed
            try:
                for frame in page.frames:
                    if frame != page.main_frame:
                        frame_dims = frame.evaluate(r"""() => ({ w: document.documentElement.scrollWidth || 800, h: document.documentElement.scrollHeight || 600 })""")
                        if frame_dims['w'] > 400 and frame_dims['h'] > 300:
                            tmp_pdf = f"tmp_page_{i}.pdf"
                            page.pdf(path=tmp_pdf, width=f"{frame_dims['w']}px", height=f"{frame_dims['h']}px", print_background=True)
                            pdfs.append(tmp_pdf)
                            break
            except:
                pass
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
