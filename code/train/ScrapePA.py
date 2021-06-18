import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import calendar
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import json
import os

from azureml.core import Workspace, Dataset

subscription_id = '3bdbda93-8c3a-472b-bdde-25e3028fc307'
resource_group = 'azure-ml'
workspace_name = 'tycho-workspace'

from azureml.core import Run
run = Run.get_context()

print("current dir")
print(os.listdir("./azureml-setup"))
print("root dir")
print(os.listdir("/mnt"))
print(os.listdir("/home"))


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

tycho_ds = Dataset.File.from_files(path='raw_data/4000posts.json')

workspace = Workspace(subscription_id, resource_group, workspace_name)

tycho_ds = tycho_ds.register(workspace=workspace,
                                 name='tycho_ds',
                                 description='tycho posts training data')

dataset = Dataset.get_by_name(workspace, name='tychowords')
dataset.download(target_path='.', overwrite=False)
