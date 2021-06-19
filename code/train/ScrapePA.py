import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import calendar
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import json
import os

from azureml.core import Workspace, Dataset

from azureml.core import Run
run = Run.get_context()

print("current dir")
print(os.listdir("."))
print("root dir")
print(os.listdir("../"))


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

if not os.path.exists('data'):
    os.makedirs('data')

file_path = "data/4000posts.json"
with open(file_path, 'w') as f:
    json.dump(texts, f)


ws = run.experiment.workspace

#dataset = Dataset.get_by_name(ws, name='tychowords')
#dataset.download(target_path='.', overwrite=False)



datastore = ws.get_default_datastore()
datastore.  
datastore.upload(src_dir='data', target_path='data', overwrite=True)
tycho_ds = Dataset.File.from_files(path = [(datastore, ('data/4000posts.json'))])

tycho_ds = tycho_ds.register(workspace=ws,
                                 name='tycho_ds',
                                 description='tycho posts training data')

#dataset = Dataset.get_by_name(workspace, name='tychowords')
#dataset.download(target_path='.', overwrite=False)
