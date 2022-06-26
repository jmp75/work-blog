---
title: "Setting up a private conda channel - part 1"
description: Research paths to set up an enterprise-wide private conda channel
comments: true
hide: false
toc: true
layout: post
hide: false
categories: [conda, conda-channel]
image: https://docs.conda.io/en/latest/_images/conda_logo.svg
author: "<a href='https://github.com/jmp75'>J-M</a>"
# permalink: /codespaces
---

# Background

I have a [conda package for compiled native libraries](https://jmp75.github.io/work-blog/recipes/conda/conda-forge/c++/2022/06/10/conda-packages-conda-forge-2.html). While it may be in a position to be submitted to conda-forge, I will also be interested at some point in setting up "my" own conda channel, with a view to distribute packages on my enterprise intranet.

This post will be a review of the possible ways to do this.

# Resources

## conda documentation

The main conda documentation has sections on [managing channels](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html) and [creating custom channels](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/create-custom-channels.html).

## fast.ai

Jeremy Howard has written the post ["fastchan, a new conda mini-distribution"](https://www.fast.ai/2021/07/15/fastconda/). It is a good read giving the rationale for setting up this channel. The repo of the [conda channel 'fastconda'](https://github.com/fastai/fastconda) has some elements of pipelines but may be a good starting point for channels hosted by Anaconda. I am not sure I can repurpose this for a private channel.

## Reusing conda-forge?

Since I intuit that a process similar to that of conda-forge could be what is emulated internally, an option may be to upfront borrow from the [conda-forge documentation](https://conda-forge.org/docs/)

The workhorse of conda-forge appears to be [using conda-smithy to manage your CI](https://conda-forge.org/docs/user/ci-skeleton.html), though that section actually rather confused me at the first read. The github [readme of conda-smithy](https://github.com/conda-forge/conda-smithy) may be a better starting point.

https://github.com/conda-forge/astra-toolbox-feedstock is a recently accepted recipe. Likely a good template to study for the swift stack.

## Commercial offerings

* At an enterprise level it may be better to use [Anaconda Server](https://server-docs.anaconda.com/en/latest/index.html) rather than cook up something. I probably cannot afford the time to trial standing one up, but my IM&T business unit may look at it. In particular, if there are use cases for sophisticated user based access controls, "free" solutions may not be up to scratch nor to scale.
* Anaconda cloud thingy
* Channel on anaconda.org

## Other

* [How To: Set up a local Conda channel for installing the ArcGIS Python API](https://support.esri.com/en/technical-article/000014951)
* [Building a Private Conda Channel](https://sionwilliams.com/posts/2019-02-04_conda_channel/)
* [Setting up a feedstock from scratch](https://gist.github.com/piyushrpt/765b4c9e5ec231cadeb78675a11cf71d)
* The github repo [Private Conda Repository](https://github.com/DanielBok/private-conda-repo) may be a good first step.

By the way one **misleading** thing if you google "How do I set up a conda channel?": the erronously titled video [How to create new channel in Anaconda (python)](https://www.youtube.com/watch?v=O_gHgjJ4Fc4) is actually demonstrating the creation of a conda environment. Skip.

## Stocktake

The first impression is that there is not a clear, single path to standing up your own conda channel over HTTP(S), no turnkey solution. The closest may be the github repo [Private Conda Repository](https://github.com/DanielBok/private-conda-repo).

## Plan

First, set up a file based channel following the conda doc for [creating custom channels](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/create-custom-channels.html). Second, try to use [PCR: Private Conda Repository](https://github.com/DanielBok/private-conda-repo).

The rest of this post will be whatever is done before dinner...

## Setting up a file based local channel

So, trying to apply [creating custom channels](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks) to the moirai library. The document is hardly a tutorial since it pops references to `package-1.0-0.tar.bz2` out of nowhere. Unless you are already familiar enough with conda-build, this leaves the reader puzzled. Anyway.

```sh
conda env list
conda activate cf # as per a previous post
which conda-build
```

[Building conda packages from scratch](https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs.html)

```sh
mkdir -p ~/src/tmp/moirai/recipe
cd ~/src/tmp/moirai/recipe
# git@github.com:jmp75/staged-recipes.git
cp ~/src/staged-recipes/recipes/moirai/* ./
ls
```

returns `bld.bat  build.sh  meta.yaml`

`conda build .` results in `PermissionError: [Errno 13] Permission denied: '/home/conda'`. This is rather poor form for a default behavior.

```sh
mkdir -p ~/src/tmp/moirai/pkgtarball/
conda build --build-only --output-folder ~/src/tmp/moirai/pkgtarball .
```

```text
conda.CondaError: Unable to create prefix directory '/home/conda/staged-recipes/build_artifacts/moirai_1655544194767/_h_env_placehold_LOTSOFTHESEPLACEHOLD_placehold_placehold_placehold_plac'.
Check that you have sufficient permissions.
```

Seriously? Leave my `/home` directory alone.

Looking at [this issue](https://github.com/conda/conda-build/issues/1331) (not quite the same context), I am trying just in case:

```sh
mkdir -p ~/src/tmp/moirai/pkgtarball/
conda build --build-only --output-folder ~/src/tmp/moirai/pkgtarball --croot ~/src/tmp/moirai/build .
```

My hopes were not very high, but thankfully this seem to complete:

```text
Total time: 0:01:57.9
CPU usage: sys=0:00:00.2, user=0:00:13.2
Maximum memory usage observed: 675.3M
Total disk usage observed (not including envs): 5.2K
```

`cd ../pkgtarball/ ; ls` shows:

`channeldata.json  icons  index.html  linux-64  noarch`

but `ls linux-64` returns `current_repodata.json  current_repodata.json.bz2  index.html  repodata_from_packages.json  repodata_from_packages.json.bz2  repodata.json  repodata.json.bz2`. Where is the expected file `moirai-1.1-h27087fc_0.tar.bz2`?

```sh
cd ~/src/tmp/moirai/pkgtarball
other_arch="osx-64 linux-32 win-32 win-64 all"
for f in $other_arch ; do
  mkdir -p $f; 
done

f=all
conda convert --platform $f ~/anaconda/conda-bld/linux-64/click-7.0-py37_0.tar.bz2 -o outputdir/

conda convert --platform all ~/anaconda/conda-bld/linux-64/click-7.0-py37_0.tar.bz2 -o outputdir/

# Wrapping up
