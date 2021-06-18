import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import calendar
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import json
import os

from azureml.core import Run
run = Run.get_context()


class return_date():
    def __init__(self):
        self.day = date.today()
    def next_date(self):
        wkdy = calendar.day_name[self.day.weekday()]
        if wkdy == 'Monday':
            self.day = self.day - timedelta(days=3)
        if (wkdy == 'Tuesday' or wkdy == 'Thursday' or wkdy == 'Saturday'):
            self.day = self.day - timedelta(days=1)
        else:
            self.day = self.day - timedelta(days=2)
        return(self.day)



d = return_date()

print(d)

day = d.next_date()

base_url = "https://www.penny-arcade.com/news/post/%d/%d/%d/" % (day.year, day.month, day.day)

texts = []
d = return_date()
while len(texts)<200:
    day = d.next_date()
    base_url = "https://www.penny-arcade.com/news/post/%d/%d/%d/" % (day.year, day.month, day.day)
    page = requests.get(base_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find(id='body')
    results = results.get_text()
    texts.append(results)
    
print(len(texts))

if not os.path.exists('raw_data'):
    os.makedirs('raw_data')

file_path = "raw_data/4000posts.json"
with open(file_path, 'w') as f:
    json.dump(texts, f)


blob_datastore_name='tychomodelstorage' # Name of the datastore to workspace
container_name='tycho-words'

from azureml.core import Workspace
ws = Workspace.from_config()
datastore = ws.get_default_datastore()

datastore.upload(
    src_dir='./raw_data',
    target_path='tycho-words/',
    overwrite=True,
    )