from fastai.text.all import *
path = untar_data(URLs.WIKITEXT)
from azureml.core import Workspace, Dataset
from azureml.core import Run
import ScrapePA

ScrapePA.main()

run = Run.get_context()

ws = run.experiment.workspace


train = pd.read_csv(path.joinpath("train.csv"),header=None)
test = pd.read_csv(path.joinpath("test.csv"), header=None)

dls_lm = DataBlock(
    blocks=(TextBlock.from_df(0, is_lm=True, seq_len=72)),
    get_x=ColReader(0)).dataloaders(train, bs=64)
dls_lm.show_batch(max_n=2)

learn = language_model_learner(
    dls_lm, AWD_LSTM, drop_mult=0.3, 
    metrics=[accuracy, Perplexity()]).to_fp16()

learn.fit_one_cycle(1, 2e-2)
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