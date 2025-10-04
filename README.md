# Canva to PDF Converter

Convert any multi-page Canva design (public view link) to a clean, multi-page PDF—without Canva's header, footer, or UI overlays—using Playwright and PyPDF2.

## Features
- Converts all pages of a Canva design to a single PDF
- Removes Canva's header, footer, and UI controls from the output
- Headless browser automation (no manual steps)
- Robust: retries on slow loads, skips failed pages, cleans up temp files

## Requirements
- Python 3.8+
- [Playwright](https://playwright.dev/python/) (with Chromium browser installed)
- [PyPDF2](https://pypdf2.readthedocs.io/)

## Installation
1. Clone this repo:
   ```bash
   git clone https://github.com/yoh-space/Design2Pdf.git
   cd src
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
   Or manually:
   ```bash
   pip install playwright PyPDF2
   playwright install chromium
   ```

### Managing the environment and dependencies

- Always keep your virtual environment out of git. A `.gitignore` is included with `venv/` ignored by default.
- Use `requirements.txt` to reproduce the runtime dependencies. To freeze your environment:
  ```bash
  pip freeze > requirements.txt
  ```
- If you need a reproducible environment across machines, consider using `pip-tools` or `poetry`.

### Pushing to GitHub (quick tips)

- Do NOT commit your `venv/` directory. If you accidentally committed it, remove it from the index and rewrite history:
  ```bash
  git rm -r --cached venv
  git commit -m "Remove venv from repo"
  git push origin main
  ```
- If the repository already contains large binaries exceeding GitHub limits (100MB), use `git-filter-repo` or `bfg` to purge them from history (see CONTRIBUTING section for steps).
- Git LFS can store very large files but is **not** recommended for virtual environments or dependencies.

## Usage
```bash
python canva_to_pdf.py <canva-view-url> [output.pdf]
```
- `<canva-view-url>`: The public Canva "view" link (should look like `https://www.canva.com/design/.../view#1`)
- `[output.pdf]`: (Optional) Output filename. Defaults to `out.pdf`.

Example:
```bash
python3 canva_to_pdf.py "https://www.canva.com/design/DAG0AX_bC4Q/q6-a02ts1GFmWJieNUElhA/view#1" my_design.pdf
```

## How it works
- Launches a headless Chromium browser for each page
- Navigates to each page of the Canva design
- Hides/removes header, footer, and UI overlays using robust DOM selectors
- Captures a PDF of just the design area for each page
- Merges all page PDFs into a single output file
- Cleans up temporary files

## Troubleshooting
- If you see timeouts or black pages, try increasing the wait time in the script or check your network connection.
- If Canva changes their UI structure, you may need to update the DOM selectors in the script.
- For very large designs, ensure your system has enough RAM and disk space.

## License
MIT License. See `LICENSE` file for details.

## Contributing
Pull requests and issues are welcome! Please open an issue for bugs or feature requests.

## Credits
- [Playwright Python](https://playwright.dev/python/)
- [PyPDF2](https://pypdf2.readthedocs.io/)

---

*This project is not affiliated with Canva. Use responsibly and respect Canva's terms of service.*
