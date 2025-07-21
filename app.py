from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

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
            page.goto(url, timeout=60000)
            page.wait_for_selector('[data-test="propertyCard"]', timeout=10000)

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            listings = soup.select('[data-test="propertyCard"]')

            for listing in listings:
                try:
                    price = listing.select_one('[data-test="propertyCard-price"]').get_text(strip=True)
                    title = listing.select_one('[data-test="propertyCard-title"]').get_text(strip=True)
                    address = listing.select_one('[data-test="propertyCard-addr"]').get_text(strip=True)
                    link = "https://www.rightmove.co.uk" + listing.select_one('a.propertyCard-link')['href']

                    features = [f.get_text(strip=True) for f in listing.select('[data-test="propertyCard-feature"]')]
                    bedrooms = next((f for f in features if "bedroom" in f.lower()), "")
                    bathrooms = next((f for f in features if "bathroom" in f.lower()), "")

                    listings_data.append({
                        "Title": title,
                        "Address": address,
                        "Price": price,
                        "Bedrooms": bedrooms,
                        "Bathrooms": bathrooms,
                        "Features": ", ".join(features),
                        "Link": link
                    })
                except:
                    continue

            browser.close()

        return jsonify({"results": listings_data})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
