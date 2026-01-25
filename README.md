# Roblox-Moderation-Tools-For-Dummies  

This project is for finding users and bad actors that should be moderated. It uses a number of Roblox's APIs to collect data. After submiting a UserID or GroupID remember to update the database (DB) before visting the Stats or Sentiment Analysis pages. This is mostly meant as a proof of concept. There are sill many flaws.

## Install
Install the requirements from requirements.txt.
Run python3, import nltk, and download 'punkt_tab' and 'stopwords':
import nltk
nltk.download('punkt_tab')
nltk.download('stopwords')

After that, start the web server by running 'web_server.py' with python.

## External Libraries
Python 3
 - flask
 - requests
 - nltk
