

import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import calendar
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import json
import os


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


if not os.path.exists('raw_data'):
    os.makedirs('raw_data')

file_path = "raw_data/4000posts.json"
with open(file_path, 'w') as f:
    json.dump(texts, f)


from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

active_directory_application_secret = os.getenv("SP_KEY")
active_directory_application_id = os.getenv("SP_ID")
active_directory_tenant_id = os.getenv("TENANT_ID")

oauth_url = "https://{}.blob.core.windows.net".format("tychomodelstorage")

from azure.identity import ClientSecretCredential
token_credential = ClientSecretCredential(
    active_directory_tenant_id,
    active_directory_application_id,
    active_directory_application_secret
)

# Instantiate a BlobServiceClient using a token credential
from azure.storage.blob import BlobServiceClient
blob_service_client = BlobServiceClient(account_url=oauth_url, credential=token_credential)

blob_client = blob_service_client.get_blob_client(container="tycho-words",blob="wordfile")

with open("raw_data/4000posts.json", "rb") as data:
    blob_client.upload_blob(data)