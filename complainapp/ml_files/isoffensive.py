# -*- coding: utf-8 -*-
"""
Created on Mon Apr 24 22:09:56 2023

@author: 97155
"""
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
import re
import emoji
def clean_text(text):
    # Remove HTML tags
    text = BeautifulSoup(text, "html.parser").get_text()
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove emojis
    text = emoji.replace_emoji(text, " ")
    # Remove punctuation
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    # Convert text to lowercase
    text = text.lower()
    # Replace repeated letters with two instances
    text = re.sub(r'(\w)\1+', r'\1\1', text)
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    words = nltk.word_tokenize(text)
    filtered_words = [word for word in words if word not in stop_words]
    # Lemmatize words
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]
    text = ' '.join(lemmatized_words)
    return text
from googleapiclient import discovery
import json
import pickle
API_KEY = "AIzaSyCiHLACkA36E_tWcaWz8WbXtLdjLiRE6ew"

client = discovery.build(
  "commentanalyzer",
  "v1alpha1",
  developerKey=API_KEY,
  discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
  static_discovery=False,
)

def is_offensive(text):
  analyze_request = {
    'comment': { 'text': text },
    'requestedAttributes': {'TOXICITY': {}}
  }

  response = client.comments().analyze(body=analyze_request).execute()
  response = response['attributeScores']['TOXICITY']['summaryScore']['value']
  if response >= 0.5: return 1
  return 0

text="pussy"
def check(text):
    hate_speech = None
    text=clean_text(text)
    words=text.split()
    with open('hate_words.txt', 'r') as file:
        hate_speech = file.read()
    hate_speech=set(hate_speech)
    for i in words:
        if i in hate_speech:
            return 1
    with open('decision_tree_model.pkl', 'rb') as file:
        clf = pickle.load(file)
    with open('count_vectorizer.pkl', 'rb') as file:
        cv = pickle.load(file)
    df=cv.transform([text]).toarray()
    if clf.predict(df)!=['No Hate and Offensive Speech']:
        return 1;
    if is_offensive(text)==1:
        return 1
    return 0
if check(text):
    print("the text is offensive")
else:
    print("the text is not offensive")