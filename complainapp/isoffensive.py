from googleapiclient import discovery
from bs4 import BeautifulSoup
import json

API_KEY = "AIzaSyCiHLACkA36E_tWcaWz8WbXtLdjLiRE6ew"

client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)


def is_offensive(text):
    text = BeautifulSoup(text, "html.parser").get_text()
    analyze_request = {
        'comment': {'text': text},
        'requestedAttributes': {'TOXICITY': {}}
    }
    try: 
        response = client.comments().analyze(body=analyze_request).execute()
        response = response['attributeScores']['TOXICITY']['summaryScore']['value']
        if response >= 0.5: return 1
        else: return 0
    except:
        return 0
