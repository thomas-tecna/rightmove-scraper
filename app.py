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

            # Set realistic headers to avoid bot detection
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
            })

            # Load the page
            page.goto(url, timeout=60000)

            # Wait for network to stabilize and then for property cards to load
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(3)  # Optional delay for Render Free tier
            page.wait_for_selector('[data-testid^="propertyCard-"]', timeout=20000)

            # Get HTML after JS has rendered
            html = page.content()
            browser.close()

        # Parse listings
        soup = BeautifulSoup(html, 'html.parser')
        listings = soup.select('[data-testid^="propertyCard-"]')

        for listing in listings:
            try:
                title = listing.select_one('[data-testid="property-title"]').get_text(strip=True) if listing.select_one('[data-testid="property-title"]') else "N/A"
                address = listing.select_one('[data-testid="property-address"] address').get_text(strip=True) if listing.select_one('[data-testid="property-address"] address') else "N/A"
                price = listing.select_one('[data-testid="property-price"]').get_text(strip=True) if listing.select_one('[data-testid="property-price"]') else "N/A"
                description = listing.select_one('[data-testid="property-description"]').get_text(strip=True) if listing.select_one('[data-testid="property-description"]') else "N/A"
                link_elem = listing.select_one('a[href*="/properties/"]')
                link = "https://www.rightmove.co.uk" + link_elem['href'] if link_elem else "N/A"

                listings_data.append({
                    "Title": title,
                    "Address": address,
                    "Price": price,
                    "Description": description,
                    "Link": link
                })
            except Exception as e:
                continue

        return jsonify({"results": listings_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
