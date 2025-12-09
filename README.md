# Description of the project
The project is a fraud detection Machine Learning model that identifies if an Iphone sales announcement is a fraud or not.
The way of using the code is explained in each section

## The Web Scraper
This file scrapes a specific sales announcements site for a specified number of Iphone sales annoucements. The code returns a .csv file with the following data sets:
Title, Description, Condition, Phone Model, Number of photos, Publisher Name, Price, Post ID and URL.
### FYI: The scraper may not work on every sales announcements sites!

## The Parser
This file receives the data sets from the Web Scraper and returns a new set of processed data set. The Parser will return the iPhone Model, Memory Size(found in the title or/and descrpition), Condition, Number of Photos, Publisher Name, Price Ratio(for the combination of the iphone, ex: iphone 14 pro, 128gb, used, has the price ratio of 0.4 means is at 40% of the market price).