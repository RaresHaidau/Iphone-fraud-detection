import import_ipynb  # Permite importul direct din .ipynb
from flask import Flask, render_template, request
import joblib
import pandas as pd
from playwright.sync_api import sync_playwright


from scraper import scrape_ad_details
# Asta va încărca clasa PhoneFraudParser direct din parser.ipynb
from parser import PhoneFraudParser 

app = Flask(__name__)

# Încărcăm modelul (presupunem că e în același folder)
try:
    model = joblib.load("fraud_model_xgb.pkl")
    print("Model loaded successfully.")
except Exception as e:
    print(f"Eroare la încărcarea modelului: {e}")
    model = None

# Funcție preluată din single_URL.py pentru formatarea datelor
def build_summary(scraped):
    summary = (
        f"URL: {scraped.get('url','')}\n"
        f"Title: {scraped.get('title','')}\n"
        f"Price: {scraped.get('price','')}\n"
        f"Rating: {scraped.get('rating','')}\n"
        f"Număr ratinguri: {scraped.get('num_ratings','')}\n"
        f"Cont OLX creat: {scraped.get('join_date','')}\n"
        f"Photos: {scraped.get('num_photos','')}\n"
        f"Attributes:\n{scraped.get('attributes','')}\n"
        f"Description:\n{scraped.get('description','')}\n"
    )
    return summary

# Funcție adaptată din single_URL.py pentru a rula în browser
def predict_web(url):
    print(f"Processing: {url}")
    
    # 1. Scraping
    scraped_data = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Apelăm funcția din scraper.py
            scraped_data = scrape_ad_details(url, page)
        except Exception as e:
            print(f"Scraping error: {e}")
        finally:
            browser.close()
            
    if not scraped_data:
        return {"error": "Nu s-au putut extrage datele. Verifică link-ul sau conexiunea."}

    # 2. Construire Summary (exact ca în single_URL.py)
    # scraper.py returnează deja un dict care conține cheia 'Summary', 
    # dar pentru siguranță folosim build_summary dacă lipsește.
    if 'Summary' in scraped_data:
        summary_text = scraped_data['Summary']
    else:
        summary_text = build_summary(scraped_data)

    # 3. Parsing (folosind clasa din parser.ipynb)
    try:
        parser = PhoneFraudParser(csv_path=None)
        parser.df_raw = pd.DataFrame({"Summary": [summary_text]})
        parser.clean()
        df_clean = parser.get_clean_df()
        
        # Selectăm coloanele necesare modelului (din single_URL.py)
        features = [
            "phone_model", "memory_size", "condition", "number_of_photos",
            "publisher_rating", "publisher_num_ratings", "clean_price", "price_ratio"
        ]
        X_new = df_clean[features]
        
        # 4. Predicție
        prediction = model.predict(X_new)[0]
        result_text = "FRAUDĂ DETECTATĂ!" if prediction == 1 else "ANUNȚ VALID (Sigur)"
        
        # Returnăm datele pentru a le afișa în HTML
        return {
            "result": result_text,
            "is_fraud": int(prediction),
            "details": df_clean.to_dict(orient='records')[0],
            "url": url
        }
        
    except Exception as e:
        return {"error": f"Eroare la procesare date: {e}"}

@app.route("/", methods=["GET", "POST"])
def index():
    data = None
    url = ""
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            data = predict_web(url)
    return render_template("index.html", data=data, url=url)

if __name__ == "__main__":
    app.run(debug=True)