# **Description of the project**
The project is a fraud detection Machine Learning model that identifies if an Iphone sales announcement is a fraud or not.
The way of using the code is explained in each section

## **The Web Scraper**
This file scrapes a specific sales announcements site for a specified number of Iphone sales announcements. The code returns a .csv file with the following data sets:
Title, Description, Condition, Phone Model, Number of photos, Publisher Name, Price, Post ID and URL.  

### **FYI:** The scraper may not work on every sales announcements site!

## **The Parser**
This file receives the data sets from the Web Scraper and returns a new set of processed data set. The Parser will return the iPhone Model, Memory Size(found in the title or/and description), Condition, Number of Photos, Publisher Name, Price Ratio(for the combination of the iphone, ex: iphone 14 pro, 128gb, used, has the price ratio of 0.4 means is at 40% of the market price).

## **The Machine Learning Model**
The ML_model.ipynb notebook handles the training logic. It uses the clean dataset provided by the Parser to train an XGBoost Classifier. The model analyzes key features such as:  

- **Price Ratio:** How much the price deviates from the median market price.  
- **Seller Reputation:** Publisher rating and number of ratings.  
- **Account Age:** Whether the account is new or established.  
- **Listing Quality:** Number of photos and description details.  

The trained model is saved as **fraud_model_xgb.pkl** and is used to predict if a new listing is "Safe" or "Fraud" (Binary Classification).

## **The Web Application**
The project includes a full-stack web interface built with Flask (**app.py**) to make the tool easy to use.  

**Backend (app.py):** Acts as the bridge between the user and the logic. It accepts a URL, triggers the Scraper to get live data, passes it to the Parser for cleaning, and finally feeds it to the ML Model for a prediction.  

**Frontend (index.html):** A simple HTML interface where users can paste an OLX link and view the fraud risk assessment along with extracted details (Model, Memory, Condition, Real Price).

## **How to Run the Project**
### **Prerequisites**
Make sure you have Python installed. You will need to install the required libraries:  
```bash
pip install flask pandas playwright scikit-learn xgboost beautifulsoup4 requests joblib import-ipynb
```

Since the scraper uses Playwright, you also need to install the necessary browser binaries:
```bash
playwright install chromium
```
## **Running the Application**
Navigate to the project folder

## **Run the Flask server:**
```bash
python app.py
```
Open your browser and go to the address provided

Paste an iPhone ad link and click "Verifică Anunțul"
