from fastai.text.all import *
path = untar_data(URLs.WIKITEXT)
from azureml.core import Workspace, Dataset
from azureml.core import Run
import ScrapePA
import torch
import mlflow.fastai
from mlflow.tracking import MlflowClient
from functools import partial
import pandas as pd
import os

ScrapePA.refresh_data()

run = Run.get_context()

ws = run.experiment.workspace

from mlflow.tracking import MlflowClient
from mlflow.entities.run import Run

class MLFlowTracking(LearnerCallback):
    "A `LearnerCallback` that tracks the loss and other metrics into MLFlow"
    def __init__(self, learn:Learner, client:MlflowClient, run_id: Run):
        super().__init__(learn)
        self.learn = learn
        self.client = client
        self.run_id = run_id
        self.metrics_names = ['train_loss', 'valid_loss'] + [o.__name__ for o in learn.metrics]

    def on_epoch_end(self, epoch, **kwargs:Any)->None:
        "Send loss and other metrics values to MLFlow after each epoch"
        if kwargs['smooth_loss'] is None or kwargs["last_metrics"] is None:
            return
        metrics = [kwargs['smooth_loss']] + kwargs["last_metrics"]
        for name, val in zip(self.metrics_names, metrics):
            self.client.log_metric(self.run_id, name, np.float(val))

mlflow_url = run.experiment.workspace.get_mlflow_tracking_uri() 
mlfclient = mlflow.tracking.MlflowClient(tracking_uri=mlflow_url)

print(torch.cuda.get_device_name(0))


train = pd.read_csv(path.joinpath("train.csv"),header=None)
test = pd.read_csv(path.joinpath("test.csv"), header=None)

dls_lm = DataBlock(
    blocks=(TextBlock.from_df(0, is_lm=True, seq_len=72)),
    get_x=ColReader(0)).dataloaders(train, bs=64)
dls_lm.show_batch(max_n=2)

learn = language_model_learner(
    dls_lm, AWD_LSTM, drop_mult=0.3, 
    metrics=[accuracy, Perplexity()]).to_fp16()

learn.fit_one_cycle(1, 2e-2, callback_fns=[partial(MLFlowTracking, client=mlfclient, run_id=run.id)])
print("trained one model")

tycho_ds = Dataset.get_by_name(ws,"tycho_ds")
if not os.path.exists('data'):
        os.makedirs('data')
tycho_ds.download("./data/",overwrite=True)
tycho = pd.read_json("data/"+os.listdir("data")[0])
tycho[0] = tycho[0].apply(lambda x: x.replace('\n', ''))
tycho[0] = tycho[0].apply(lambda x: x[145:])

t_dls = DataBlock(
    blocks=(TextBlock.from_df(0, is_lm=True, seq_len=72)),
    get_x=ColReader(0)).dataloaders(tycho, bs=64)
t_dls.show_batch(max_n=2)

learn = language_model_learner(
    t_dls, AWD_LSTM, drop_mult=0.3, 
    metrics=[accuracy, Perplexity()]).to_fp16()

#learn = learn.load('wiki103')
learn.unfreeze()
learn.fit_one_cycle(10, 2e-3)

learn.save('tycho_model')
print("trained tycho model")