from fastai.text.all import *
from fastai.callback.core import Callback
from azureml.core import Workspace, Dataset, Run
import ScrapePA
import torch
from functools import partial
import pandas as pd
import os

run = Run.get_context()

#source or refresh domain specific language data
ScrapePA.check_data(run)

ws = run.experiment.workspace

#custom logging to emit loss to AML every 5% of training completion
class AML_Logging(Callback):
    def __init__(self, run_name):
        self.pct_c = 0
        self.run_name = run_name
    def after_batch(self):
        rounded_pct = round(self.pct_train,3)
        if rounded_pct % .005 == 0:
            if rounded_pct > self.pct_c:
                self.pct_c = rounded_pct
                run.log(self.run_name, self.loss.tolist())

#check to make sure using cuda
print(torch.cuda.get_device_name(0))

#load generic training data from imdb
path = untar_data(URLs.IMDB)
get_imdb = partial(get_text_files, folders=['train', 'test', 'unsup'])

dls_lm = DataBlock(
    blocks=TextBlock.from_folder(path, is_lm=True),
    get_items=get_imdb, splitter=RandomSplitter(0.1)
).dataloaders(path, path=path, bs=128, seq_len=80)


#setup language model and fit
learn = language_model_learner(dls_lm, AWD_LSTM, drop_mult=0.3, metrics=[accuracy, Perplexity()]).to_fp16()
learn.fit_one_cycle(1, 2e-2,cbs=[AML_Logging("wiki train loss")])

#evaluate validation metrics
results = learn.validate()
valid_metrics = ["loss"]
[valid_metrics.append(i.name) for i in learn.metrics]
for i in range(len(valid_metrics)):
    run.log("wiki validation "+valid_metrics[i], results[i])

print("trained one model")

TEXT = "I liked this movie because"
N_WORDS = 40
N_SENTENCES = 2
preds = [learn.predict(TEXT, N_WORDS, temperature=0.75) 
         for _ in range(N_SENTENCES)]
print("\n".join(preds))


#load domain specific text from Azure datasets
tycho_ds = Dataset.get_by_name(ws,"tycho_ds")
if not os.path.exists('data'):
        os.makedirs('data')
tycho_ds.download("./data/",overwrite=True)
tycho = pd.read_json("data/"+os.listdir("data")[0])
tycho[0] = tycho[0].apply(lambda x: x.replace('\n', ''))
tycho[0] = tycho[0].apply(lambda x: x[145:])

#create data block
t_dls = DataBlock(
    blocks=(TextBlock.from_df(0, is_lm=True, seq_len=72)),
    get_x=ColReader(0)).dataloaders(tycho, bs=64)
t_dls.show_batch(max_n=2)


learn.dls = t_dls

learn.unfreeze()
learn.fit_one_cycle(10, 2e-3,cbs=[AML_Logging("tycho train loss")])

results = learn.validate()
valid_metrics = ["loss"]
[valid_metrics.append(i.name) for i in learn.metrics]
for i in range(len(valid_metrics)):
    run.log("tycho validation "+valid_metrics[i], results[i])

learn.save('tycho_model')
print("trained tycho model")

TEXT = "Gabriel really likes"
N_WORDS = 300
N_SENTENCES = 2
preds = [learn.predict(TEXT, N_WORDS, temperature=0.75) 
         for _ in range(N_SENTENCES)]