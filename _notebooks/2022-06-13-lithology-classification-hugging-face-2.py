# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: Hugging Face
#     language: python
#     name: hf
# ---

# %% [markdown]
# # Lithology classification using Hugging Face, part 2
#
# - toc: true
# - badges: true
# - comments: true
# - categories: [hugging-face, NLP, lithology]
# - author: J-M
#

# %% [markdown]
# # About
#
# This is a continuation of [Lithology classification using Hugging Face, part 1](https://jmp75.github.io/work-blog/hugging-face/nlp/lithology/2022/06/01/lithology-classification-hugging-face.html).
#
# We saw in the previous post that the Namoi lithology logs data had their primary (major) lithology mostly completed. A substantial proportion had the label `None` nevertheless, despite descriptions that looked like they would obviously lead to a categorisation. There were many labels, with a long-tailed frequency histogram.
#
# The aim of this post is (was) to get a classification training happening.
#
# __Spoiler alert: it won't__. Almost.
#
# Rather than write a post after the fact pretending it was a totally smooth journey, the following walktrough _deliberately_ keeps and highlights issues, albeit succinctly. **Don't** jump to the conclusion that we will not get there eventually, or that Hugging Face is not good. When you adapt prior work to your own use case, you **will** likely stumble, so this post will make you feel in good company.

# %% [markdown]
# # Kernel installation
#
# The previous post was about data exploration and used mostly facilities such as pandas, not any deep learning related material. This post will, so we need to install Hugging Face. I did bump into a couple of issues while trying to get an environment going. I will not give the full grubby details, but highlight upfront a couple of things:
#
# * Do create a new dedicated conda environment for your work with Hugging Face, even if you already have an environment with e.g. pytorch you'd like to reuse.
# * The version 4.11.3 of HF `transformers` on the conda channel `huggingface`, at the time of writing, has a [bug](https://github.com/nlp-with-transformers/notebooks/issues/31). You should install the packages from the `conda-forge` channel.
#
# In a nutshell, for Linux:
#
# ```sh
# myenv=hf
# mamba create -n $myenv python=3.9 -c conda-forge
# mamba install -n $myenv --yes ipykernel matplotlib sentencepiece scikit-learn -c conda-forge
# mamba install -n $myenv --yes pytorch=1.11 -c pytorch -c nvidia -c conda-forge
# mamba install -n $myenv --yes torchvision torchaudio -c pytorch -c nvidia -c conda-forge
# mamba install -n $myenv --yes -c conda-forge datasets transformers
# conda activate $myenv
# python -m ipykernel install --user --name $myenv --display-name "Hugging Face"
# ```
#
# and in Windows:
#
# ```bat
# set myenv=hf
# mamba create -n %myenv% python=3.9 -c conda-forge
# mamba install -n %myenv% --yes ipykernel matplotlib sentencepiece scikit-learn -c conda-forge
# mamba install -n %myenv% --yes pytorch=1.11 -c pytorch -c nvidia -c conda-forge
# mamba install -n %myenv% --yes torchvision torchaudio -c pytorch -c nvidia -c conda-forge
# mamba install -n %myenv% --yes -c conda-forge datasets transformers
# conda activate %myenv%
# python -m ipykernel install --user --name %myenv% --display-name "Hugging Face"
# ```
#

# %% [markdown]
# # Walkthrough
#
# Let's get on with all the imports upfront (not obvious, mind you, but after the fact...)

# %%
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from pathlib import Path
from datasets import ClassLabel
from transformers import TrainingArguments, Trainer
from sklearn.metrics import f1_score
from collections import Counter

# Some column string identifiers
MAJOR_CODE = "MajorLithCode"
MAJOR_CODE_INT = "MajorLithoCodeInt"  # We will create a numeric representation of labels, which is (I think?) required by HF.
MINOR_CODE = "MinorLithCode"
DESC = "Description"

# %%
fn = Path("~").expanduser() / "data/ela/shp_namoi_river/NGIS_LithologyLog.csv"
litho_logs = pd.read_csv(
    fn, dtype={"FromDepth": str, "ToDepth": str, MAJOR_CODE: str, MINOR_CODE: str}
)

# To avoid importing from the ela package, copy a couple of functions:
# from ela.textproc import token_freq, plot_freq


def token_freq(tokens, n_most_common=50):
    list_most_common = Counter(tokens).most_common(n_most_common)
    return pd.DataFrame(list_most_common, columns=["token", "frequency"])


def plot_freq(dataframe, y_log=False, x="token", figsize=(15, 10), fontsize=14):
    """Plot a sorted histogram of work frequencies

    Args:
        dataframe (pandas dataframe): frequency of tokens, typically with colnames ["token","frequency"]
        y_log (bool): should there be a log scale on the y axis
        x (str): name of the columns with the tokens (i.e. words)
        figsize (tuple):
        fontsize (int):

    Returns:
        barplot: plot

    """
    p = dataframe.plot.bar(x=x, figsize=figsize, fontsize=fontsize)
    if y_log:
        p.set_yscale("log", nonposy="clip")
    return p


litho_classes = litho_logs[MAJOR_CODE].values
df_most_common = token_freq(litho_classes, 50)
plot_freq(df_most_common)


# %% [markdown]
#
# ## Imbalanced data sets
#
# From the histogram above, it is pretty clear that labels are also not uniform an we have a class imbalance. Remember to skim [Lithology classification using Hugging Face, part 1](https://jmp75.github.io/work-blog/hugging-face/nlp/lithology/2022/06/01/lithology-classification-hugging-face.html) for the initial data exploration if you have not done so already.
#
# For the sake of the exercise in this post, I will reduce arbitrarily the number of labels used in this post, by just "forgetting" the less represented classes.
#
# There are many resources about class imbalances. One of them is [8 Tactics to combat imbalanced classes in your machine learning dataset](https://machinelearningmastery.com/tactics-to-combat-imbalanced-classes-in-your-machine-learning-dataset)
#
# Let's see what labels we may want to keep for this post:
#


# %%
def sample_desc_for_code(major_code, n=50, seed=None):
    is_code = litho_logs[MAJOR_CODE] == major_code
    coded = litho_logs.loc[is_code][DESC]
    if seed is not None:
        np.random.seed(seed)
    return coded.sample(n=50)


# %%
sample_desc_for_code("UNKN", seed=123)

# %% [markdown]
# The "unknown" category is rather interesting in fact, and worth keeping as a valid class.

# %% [markdown]
# ## Subsetting
#
# Let's keep "only" the main labels, for the sake of this exercise. We will remove None however, despite its potential interest. We will (hopefully) revisit this in another post.

# %%
labels_kept = df_most_common["token"][:17].values  # 17 first classes somewhat arbitraty
labels_kept = labels_kept[labels_kept != "None"]
labels_kept

# %%
kept = [x in labels_kept for x in litho_classes]
litho_logs_kept = litho_logs[kept].copy()  # avoid warning messages down the track.
litho_logs_kept.sample(10)


# %%
labels = ClassLabel(names=labels_kept)
litho_logs_kept[MAJOR_CODE_INT] = [
    labels.str2int(x) for x in litho_logs_kept[MAJOR_CODE].values
]

# %% [markdown] tags=[]
# ## Class imbalance
#
# Even our subset of 16 classes is rather imbalanced; the number of "clay" labels is looking more than 30 times that of "coal" just by eyeballing.
#
# The post by Jason Brownlee [8 Tactics to Combat Imbalanced Classes in Your Machine Learning Dataset](https://machinelearningmastery.com/tactics-to-combat-imbalanced-classes-in-your-machine-learning-dataset), outlines several approaches. One of them is to resample from labels, perhaps with replacement, to equalise classes. It is a relatively easy approach to implement, but there are issues, growing with the level of imbalance. Notably, if too many rows from underrepresented classes are repeated, there is an increased tendency to overfitting at training.
#
# The video [Simple Training with the 🤗 Transformers Trainer (at 669 seconds)](https://youtu.be/u--UVvH-LIQ?t=669) also explains the issues with imbalances and crude resampling. It offers instead a solution with class weighting that is more robust. That approach is evoked in Jason's post, but the video has a "Hugging Face style" implementation ready to repurpose.
#
# ### Resample with replacement
#
# Just for information, what we'd do with a relatively crude resampling may be:
#

# %%
def sample_major_lithocode(dframe, code, n=10000, seed=None):
    x = dframe[dframe[MAJOR_CODE] == code]
    replace = n > len(x)
    return x.sample(n=n, replace=replace, random_state=seed)


# %%
sample_major_lithocode(litho_logs_kept, "CLAY", n=10, seed=0)

# %% tags=[]
balanced_litho_logs = [
    sample_major_lithocode(litho_logs_kept, code, n=10000, seed=0)
    for code in labels_kept
]
balanced_litho_logs = pd.concat(balanced_litho_logs)
balanced_litho_logs.head()

# %%
plot_freq(token_freq(balanced_litho_logs[MAJOR_CODE].values, 50))

# %% [markdown] tags=[]
# ### Dealing with imbalanced classes with weights
#
# Instead of the resampling above, we adapt the approach creating weights for the Trainer we will run.
#

# %%
sorted_counts = litho_logs_kept[MAJOR_CODE].value_counts().sort_index()
sorted_counts

# %%
sorted_counts / sorted_counts.sum()

# %%
class_weights = (1 - sorted_counts / sorted_counts.sum()).values
class_weights

# %% [markdown] tags=[]
#
# We check that cuda is available (of course optional)
#

# %%
assert torch.cuda.is_available()

# %% [markdown] tags=[]
#
# On Linux if you have a DELL laptop with an NVIDIA card, but `nvidia-smi` returns: `NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. Make sure that the latest NVIDIA driver is installed and running`, you may need to change your kernel specification file $HOME/.local/share/jupyter/kernels/hf/kernel.json. This behavior seems to depend on the version of Linux kernel you have. It certainly changed out of the blue for me from yesterday, despite no change that I can tell.
#
# `optirun nvidia-smi` returning a proper graphic card report should be a telltale sign you have to update your kernel.json like so:
#
# ```json
# {
#  "argv": [
#   "optirun",
#   "/home/your_ident/miniconda/envs/hf/bin/python",
#   "-m",
#   "ipykernel_launcher",
#   "-f",
#   "{connection_file}"
#  ],
#  "display_name": "Hugging Face",
#  "language": "python",
#  "metadata": {
#   "debugger": true
#  }
# }
# ```
#
# You may need to restart jupyter-lab, or visual studio code, etc., for change to take effect. Restarting the kernel may not be enough, conter-intuitively.
#
# Background details about optirun architecture at [Bumblebee Debian]https://wiki.debian.org/Bumblebee


# %%
class_weights = torch.from_numpy(class_weights).float().to("cuda")
class_weights

# %%
model_nm = "microsoft/deberta-v3-small"

# %% [markdown]
#
# ## Tokenisation
#
# ### Bump on the road; download operations taking too long
#
# At this point I spent more hours than I wish I had on an issue, perhaps very unusual.
#
# The operation `tokz = AutoTokenizer.from_pretrained(model_nm)` was taking an awful long time to complete:
#
# ```text
# CPU times: user 504 ms, sys: 57.9 ms, total: 562 ms
# Wall time: 14min 13s
# ```
#
# To cut a long story short, I managed to figure out what was going on. It is documented on the Hugging Face forum at: [Some HF operations take an excessively long time to complete](https://discuss.huggingface.co/t/some-hf-operations-take-an-excessively-long-time-to-complete/18986). If you have issues where HF operations take a long time, read it.
#
# Now back to the tokenisation story. Note that the local caching may be superflous if you do not encounter the issue just mentioned.

# %%
p = Path("./tokz_pretrained")
if p.exists():
    tokz = AutoTokenizer.from_pretrained(p)
else:
    tokz = AutoTokenizer.from_pretrained(model_nm)
    tokz.save_pretrained("./tokz_pretrained")

# %% [markdown]
# Let's see what this does on a typical lithology description

# %%
tokz.tokenize("CLAY, VERY SANDY")

# %% [markdown]
# Well, the vocabulary is probably case sensitive and all the descriptions being uppercase in the source data are likely problematic. Let's check what happens on lowercase descriptions:

# %%
tokz.tokenize("clay, very sandy")

# %% [markdown]
# This looks better. So let's change the descriptions to lowercase; we are not loosing any relevent information in this case, I think.

# %%
# note: no warnings because we used .copy() earlier to create litho_logs_kept
litho_logs_kept[DESC] = litho_logs_kept[DESC].str.lower()

# %%
litho_logs_kept_mini = litho_logs_kept[[MAJOR_CODE_INT, DESC]]
litho_logs_kept_mini.sample(n=10)


# %% [markdown]
# ## Create dataset and tokenisation
#
# We want to create a dataset such that tokenised data is of uniform shape (better for running on GPU)
# Applying the technique in [this segment of the HF course video](https://youtu.be/_BZearw7f0w?list=PLo2EIpI_JMQvWfQndUesu0nPBAtZ9gP1o&t=150). Cheating a bit on guessing the length (I know from offline checks that max is 90 tokens)

# %%
ds = Dataset.from_pandas(litho_logs_kept_mini)

max_length = 128


def tok_func(x):
    return tokz(
        x[DESC],
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )


# %% [markdown]
# The Youtube video above suggests to use `tok_ds = ds.map(tok_func, batched=True)` for a faster execution; however I ended up with the foollowing error:
#
# ```text
# TypeError: Provided `function` which is applied to all elements of table returns a `dict` of types [<class 'torch.Tensor'>, <class 'torch.Tensor'>, <class 'torch.Tensor'>]. When using `batched=True`, make sure provided `function` returns a `dict` of types like `(<class 'list'>, <class 'numpy.ndarray'>)`.
# ```
#
# The following non-batched option works in a reasonable time:

# %%
tok_ds = ds.map(tok_func)

# %%
tok_ds_tmp = tok_ds[:5]
tok_ds_tmp.keys()

# %%
# check the length of vectors is indeed 128:
len(tok_ds_tmp["input_ids"][0][0])

# %%
num_labels = len(labels_kept)

# %%
# NOTE: the local caching may be superflous
p = Path("./model_pretrained")
if p.exists():
    model = AutoModelForSequenceClassification.from_pretrained(p, num_labels=num_labels)
else:
    model = AutoModelForSequenceClassification.from_pretrained(
        model_nm, num_labels=num_labels
    )
    model.save_pretrained(p)

# %%
print(type(model))


# %%
# Different approach, but one that I am not sure how to progress to a hugging face Dataset. Borrowed from [this video](https://youtu.be/1pedAIvTWXk?list=PLo2EIpI_JMQvWfQndUesu0nPBAtZ9gP1o&t=143)
# litho_desc_list = [x for x in litho_logs_kept_mini[DESC].values]
# input_descriptions = tokz(litho_desc_list, padding=True, truncation=True, max_length=256, return_tensors='pt')
# input_descriptions['input_ids'].shape
# model(input_descriptions['input_ids'][:5,:], attention_mask=input_descriptions['attention_mask'][:5,:]).logits

# %%
tok_ds

# %% [markdown]
# Transformers always assumes that your labels has the column name "labels". Odd, but at least this fosters a consistent system, so why not:

# %%
tok_ds = tok_ds.rename_columns({MAJOR_CODE_INT: "labels"})

# %%
# We want to make sure we work on the GPU, so at least make sure we have torch tensors.
# Note that HF is supposed to take care of movind data to the GPU if available, so you should not ahve to manually copy the data to the GPU device
tok_ds.set_format("torch")

# %%
# args = TrainingArguments(output_dir='./litho_outputs', learning_rate=lr, warmup_ratio=0.1, lr_scheduler_type='cosine', fp16=True,
#     evaluation_strategy="epoch", per_device_train_batch_size=bs, per_device_eval_batch_size=bs*2,
#     num_train_epochs=epochs, weight_decay=0.01, report_to='none')

# %%
dds = tok_ds.train_test_split(0.25, seed=42)

# %%
# https://huggingface.co/docs/transformers/training

# %%
# from Jeremy's notebook:
# def compute_metrics(eval_pred):
#     logits, labels = eval_pred
#     predictions = np.argmax(logits, axis=-1)
#     return metric.compute(predictions=predictions, references=labels)

# %%
# Defining the Trainer to compute Custom Loss Function, adapted from [Simple Training with the 🤗 Transformers Trainer, around 840 seconds](https://youtu.be/u--UVvH-LIQ?t=840)
class WeightedLossTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        # Feed inputs to model and extract logits
        outputs = model(**inputs)
        logits = outputs.get("logits")
        # Extract Labels
        labels = inputs.get("labels")
        # Define loss function with class weights
        loss_func = torch.nn.CrossEntropyLoss(weight=class_weights)
        # Compute loss
        loss = loss_func(logits, labels)
        return (loss, outputs) if return_outputs else loss


# %%
def compute_metrics(eval_pred):
    labels = eval_pred.label_ids
    predictions = eval_pred.predictions.argmax(-1)
    f1 = f1_score(labels, predictions, average="weighted")
    return {"f1": f1}


# %%
output_dir = "./hf_training"
batch_size = 128
epochs = 5
lr = 8e-5

# %%
training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=epochs,
    learning_rate=lr,
    lr_scheduler_type="cosine",
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size * 2,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    logging_steps=len(dds["train"]),
    fp16=True,
    push_to_hub=False,
    report_to="none",
)


# %%
model = model.to("cuda:0")

# %% [markdown]
# The above nay not be strictly necessary, depending on your version of `transformers`. I bumped into the following issue, which was probably the transformers [4.11.3 bug](https://github.com/nlp-with-transformers/notebooks/issues/31#issuecomment-1075369210): `RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu! (when checking argument for argument index in method wrapper__index_select)`

# %%
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dds["train"],
    eval_dataset=dds["test"],
    tokenizer=tokz,
    compute_metrics=compute_metrics,
)

# %% [markdown]
# ## Training?
#
# You did read the introduction and its spoiler alert, right? 

# %%
trainer.train()

# %% [markdown] tags=[]
# # Stocktake and conclusion
#
# So, as announced at the start of this post, we hit a pothole in our journey. 
#
# ```text
# RuntimeError: The size of tensor a (768) must match the size of tensor b (128) at non-singleton dimension 3
# ```
#
# Where the number (768) comes from is a bit of a mystery. I gather from Googling that this may have to do with the embedding of the Deberta model we are trying to fine tune, but I may be off the mark.
#
# It is probably something at which an experience NLP practitioner will roll their eyes.
#
# That's OK, We'll get there.

# %%
