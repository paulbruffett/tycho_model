import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import calendar
import json
import os

from azureml.core import Workspace, Dataset

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


def refresh_data():
    d = return_date()

    print(d)

    day = d.next_date()

    base_url = "https://www.penny-arcade.com/news/post/%d/%d/%d/" % (day.year, day.month, day.day)

    texts = []
    d = return_date()
    while len(texts)<3500:
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

def upload_dataset(ws, new_version=False):
    datastore = ws.get_default_datastore()
    datastore.upload(src_dir='data', target_path='data', overwrite=True)
    tycho_ds = Dataset.File.from_files(path = [(datastore, ('data/4000posts.json'))])

    tycho_ds = tycho_ds.register(workspace=ws,
                                    name='tycho_ds',
                                    description='tycho posts training data',
                                    create_new_version=new_version)

    tycho_ds.add_tags({"created_on": date.today().isoformat()})

if __name__ == "__main__":
    ws = run.experiment.workspace

    try:
        #does the dataset exist?
        tycho_ds = Dataset.get_by_name(ws,"tycho_ds")
        print("Dataset Exists")
        new_version = True
    except:
        print("Dataset doesn't exist")
        new_version = False

    #is the dataset older than 6 days?
    dataset_time = date.fromisoformat(tycho_ds.tags['created_on'])
    time_delta = date.today() - dataset_time
    if time_delta.days > 6:
        print("Dataset is older than 6 days")
        refresh_data()
        upload_dataset(ws, new_version=new_version)
    else:
        print("Dataset is not older than 6 days")