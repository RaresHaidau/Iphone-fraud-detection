import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin
import csv
from playwright.sync_api import sync_playwright

BASE_URL = 'https://www.olx.ro'
SEARCH_URL = 'https://www.olx.ro/electronice-si-electrocasnice/telefoane-mobile/iphone/q-telefoane/?currency=RON'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ---------------- LOGICĂ DE RATING (FINAL ȘI CORECT) ----------------
def get_rating_with_playwright(page, ad_url):
    """
    Extrage ratingul folosind Playwright. Utilizează metoda .nth(0) pentru a rezolva
    ambiguitatea selectorului fără a folosi selectori CSS nestandard.
    """
    RATING_NOT_FOUND = "N/A"
    try:
        page.goto(ad_url, timeout=60000)
        
        # Selectorul ambițios, dar care va fi filtrat cu .nth(0)
        # Găsește TOATE tagurile <p> din widget-ul principal (găsește 2)
        AMBIGUOUS_SELECTOR = "[data-testid='main'] [data-testid='user-score-widget'] p"
        
        # Obținem locatorul pentru PRIMUL element din listă, care este scorul (4.7 / 5)
        rating_locator = page.locator(AMBIGUOUS_SELECTOR).nth(0)
        
        # Așteptăm ca acest locator unic să fie vizibil și populat cu text
        rating_locator.wait_for(state="visible", timeout=10000)
        
        # Extrage textul direct din locatorul unic
        rating_text = rating_locator.inner_text()
        
        # Curățăm și extragem numerele (logica robustă)
        rating_text_cleaned = re.sub(r'[^\d\.\/]', ' ', rating_text).strip()
        scores = re.findall(r'(\d+\.?\d*)', rating_text_cleaned)
            
        if len(scores) >= 2:
            rating = f"{scores[0]} / {scores[-1]}"
            print(f"   [Rating GĂSIT: {rating}]")
            return rating
        
        # Dacă s-a găsit elementul, dar nu și numerele
        print(f"   [Rating N/A: Scorul nu a putut fi format din textul: {rating_text_cleaned}]")
        return RATING_NOT_FOUND
             
    except Exception as e:
        print(f"   [Eroare Playwright la extragerea Ratingului. Eroare: {e}]")
        # Putem verifica dacă pagina conține textul "Nu are încă ratinguri"
        if "Nu are încă ratinguri" in page.content():
            return "N/A - Fără Rating"
        
        return RATING_NOT_FOUND

# ---------------- Funcțiile auxiliare (fără modificări) ----------------

def get_ad_links_from_page(url):
    ad_links = []
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for a in soup.find_all('a', href=re.compile(r'/d/oferta/')):
            href = a.get('href')
            if not href:
                continue
            link = urljoin(BASE_URL, href.split('#')[0])
            if link not in ad_links:
                ad_links.append(link)

    except Exception as e:
        print(f"Error fetching {url}: {e}")

    return ad_links


# ---------------- LOGICĂ DE VIEWS ----------------
def get_number_of_ratings_with_playwright(page, ad_url):
    """
    Extrage numărul de ratinguri.
    """
    RATING_COUNT_NOT_FOUND = "N/A"
    try:
        page.goto(ad_url, timeout=60000)

        # Selector pentru elementele din widget-ul user
        USER_WIDGET_SELECTOR = "[data-testid='main'] [data-testid='user-score-widget'] p"

        # Al doilea <p> din widget-ul user conține de obicei nr de ratinguri
        rating_count_locator = page.locator(USER_WIDGET_SELECTOR).nth(1)
        rating_count_locator.wait_for(state="visible", timeout=10000)

        rating_count_text = rating_count_locator.inner_text().strip()
        if rating_count_text:
            print(f"   [Număr ratinguri GĂSIT: {rating_count_text}]")
            return rating_count_text
        else:
            return RATING_COUNT_NOT_FOUND

    except Exception as e:
        print(f"   [Eroare la extragerea numărului de ratinguri: {e}]")
        return RATING_COUNT_NOT_FOUND


def get_account_start_with_playwright(page, ad_url):
    """
    Extrage luna și anul în care contul OLX a fost creat.
    Caută textul exact 'Pe OLX din ...' în pagina anunțului.
    """
    NOT_FOUND = "N/A"
    try:
        page.goto(ad_url, timeout=60000)
        time.sleep(1)  # scurt delay ca să încarce widget-ul complet

        # Găsește TOATE elementele care conțin text
        elements = page.locator("p, span, div").all_inner_texts()

        for text in elements:
            if "Pe OLX din" in text:
                match = re.search(r"Pe OLX din ([a-zA-ZăîâșțĂÎÂȘȚ]+ \d{4})", text)
                if match:
                    start_date = match.group(1)
                    print(f"   [Cont OLX creat: {start_date}]")
                    return start_date

        return NOT_FOUND

    except Exception as e:
        print(f"   [Eroare la extragerea lunii/anului contului OLX: {e}]")
        return NOT_FOUND



def scrape_ad_details(ad_url, page):
    # Extragerea detaliilor prin Requests
    try:
        response = requests.get(ad_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        parent_div = soup.find('div', attrs={'data-testid': 'offer_title'})
        title_el = parent_div.find('h4') if parent_div else soup.find(['h1', 'h2'])
        title = title_el.get_text(strip=True) if title_el else 'N/A'
        price_el = soup.find('h3')
        price = price_el.get_text(strip=True) if price_el else 'N/A'
        desc = soup.find('div', attrs={'data-testid': 'ad_description'})
        description = desc.get_text(separator=' ', strip=True) if desc else 'N/A'
        photos = len(soup.select("div[data-testid='ad-photo']"))
        
        attributes_list = []
        details_container = soup.find('div', attrs={'data-testid': 'ad-parameters-container'})
        if details_container:
            for p in details_container.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    attributes_list.append(text)
        attributes = ' | '.join(attributes_list) if attributes_list else 'N/A'
        
    except Exception as e:
        print(f"Error scraping details from {ad_url} with Requests: {e}")
        return None
        
    # Extragerea RATING-ului prin Playwright (funcția de mai sus)
    rating = get_rating_with_playwright(page, ad_url)
    number_of_ratings = get_number_of_ratings_with_playwright(page, ad_url)
    account_start = get_account_start_with_playwright(page, ad_url)


    return {
   # 'URL': ad_url,
    #'Title': title,
    #'Price': price,
    'Summary': f"URL: {ad_url}\n"
               f"Title:{title}\n" 
               f"Price: {price}\n"
               f"Rating: {rating}\n"
               f"Număr ratinguri: {number_of_ratings}\n"
               f"Cont OLX creat: {account_start}\n"
               f"Photos: {photos}\n"
               f"Attributes:\n{attributes}\n"
               f"Description:\n{description}"
}


def save_to_csv(data, filename="olx_ads_data.csv"):
    if not data:
        print("Nu există date de salvat.")
        return

    fieldnames = list(data[0].keys())

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                lineterminator='\n',
                quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            writer.writerows(data)

        print(f"\n✅ Datele au fost salvate cu succes în '{filename}'")
    except Exception as e:
        print(f"\n❌ Eroare la salvarea fișierului CSV: {e}")


# ---------------- MAIN ----------------
def main():
    all_links = []

    for page_nr in range(1, 7):
        url = SEARCH_URL + f"&page={page_nr}"
        print(f"Se extrag linkuri de pe pagina {page_nr}...")
        all_links.extend(get_ad_links_from_page(url))
        time.sleep(1)

    unique_links = list(dict.fromkeys(all_links))
    print(f"Am găsit {len(unique_links)} linkuri unice de anunțuri.")

    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page(user_agent=HEADERS['User-Agent']) 

        print("\nÎncepe extragerea detaliilor...")
        for i, link in enumerate(unique_links):
            print(f"Scraping anunț {i+1}/{len(unique_links)}: {link}")
            
            data = scrape_ad_details(link, page)
            if data:
                results.append(data)
            
            time.sleep(1)

        browser.close()
        
    save_to_csv(results)


if __name__ == "__main__":
    main()