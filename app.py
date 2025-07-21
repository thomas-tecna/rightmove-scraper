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
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Mimic a real browser
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
            })

            # Load the page
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(2)

            try:
                page.wait_for_selector('[data-testid^="propertyCard-"]', timeout=20000, state="attached")
            except:
                print("⚠️ Property cards not visibly rendered — continuing anyway")

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')

        # Try primary selector
        listings = soup.select('[data-testid^="propertyCard-"]')

        # Fallback: use legacy/classic structure if primary yields few results
        if not listings or len(listings) < 2:
            print(f"⚠️ Found only {len(listings)} listings with primary selector. Trying fallback selectors.")
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
