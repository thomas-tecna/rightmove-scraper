from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

@app.route("/scrape", methods=["GET"])
def scrape_rightmove():
    url = request.args.get("url")
    if not url or "rightmove.co.uk" not in url:
        return jsonify({"error": "Invalid or missing URL"}), 400

    listings_data = []

    try:
        with sync_playwright() as p:
            # ✅ Render-safe launch (no sandbox)
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()

            # Mimic a real browser
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
            })

            # Go to the page and wait for load
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=20000)

            # ✅ Wait until listings are visible in DOM
            page.wait_for_selector('[data-testid^="propertyCard-"]', state="visible", timeout=30000)
            time.sleep(1.5)  # Give time for JS to finish rendering

            html = page.content()
            browser.close()

        # ✅ Optional: dump raw HTML for debug
        with open("/tmp/debug.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, 'html.parser')

        # Primary selector
        listings = soup.select('[data-testid^="propertyCard-"]')

        # Fallback if needed
        if not listings or len(listings) < 2:
            print(f"⚠️ Found only {len(listings)} listings. Trying fallback selectors.")
            fallback = soup.select('div.propertyCard, div[data-test="propertyCard"], div[data-testid*="propertyCard"]')
            if len(fallback) > len(listings):
                listings = fallback

        for listing in listings:
            try:
                title = listing.select_one('[data-testid="property-title"]')
                address = listing.select_one('[data-testid="property-address"] address')
                price = listing.select_one('[data-testid="property-price"]')
                description = listing.select_one('[data-testid="property-description"]')
                link_elem = listing.select_one('a[href*="/properties/"]')

                listings_data.append({
                    "Title": title.get_text(strip=True) if title else "N/A",
                    "Address": address.get_text(strip=True) if address else "N/A",
                    "Price": price.get_text(strip=True) if price else "N/A",
                    "Description": description.get_text(strip=True) if description else "N/A",
                    "Link": "https://www.rightmove.co.uk" + link_elem['href'] if link_elem else "N/A"
                })
            except Exception as e:
                continue

        return jsonify({"results": listings_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
