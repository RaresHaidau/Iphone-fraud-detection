import import_ipynb
import joblib
import pandas as pd
from scraper import scrape_ad_details
from parser import PhoneFraudParser
from playwright.sync_api import sync_playwright

MODEL_PATH = "/home/haidau_rares/projects/fraud_detection_iphones/fraud_model_xgb.pkl"

model = joblib.load(MODEL_PATH)

def scrape_single_ad(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        result = scrape_ad_details(url, page)
        browser.close()
        return result

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

def parse_single_listing(summary_text, parser_class=PhoneFraudParser):
    parser = parser_class(csv_path=None)
    parser.df_raw = pd.DataFrame({"Summary": [summary_text]})
    parser.clean()
    df_clean = parser.get_clean_df()
    features = [
        "phone_model",
        "memory_size",
        "condition",
        "number_of_photos",
        "publisher_rating",
        "publisher_num_ratings",
        "clean_price",
        "price_ratio"
    ]
    return df_clean[features]

def predict_from_url(url: str):
    print(f"\nChecking listing:\n{url}\n")
    scraped = scrape_single_ad(url)
    if scraped is None:
        print("Could not scrape the listing.")
        return
    summary_text = build_summary(scraped)
    X_new = parse_single_listing(summary_text)
    prediction = model.predict(X_new)[0]
    if prediction == 1:
        print("Fraud")
    else:
        print("Not Fraud")

if __name__ == "__main__":
    test_url = input("Enter OLX URL to check: ").strip()
    predict_from_url(test_url)
