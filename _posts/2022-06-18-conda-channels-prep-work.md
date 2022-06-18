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

I have a [conda package for a compiled native library (moirai)](https://jmp75.github.io/work-blog/recipes/conda/conda-forge/c++/2022/06/10/conda-packages-conda-forge-2.html). While it may be in a position to be submitted to conda-forge, I will also be interested at some point in setting up "my" own conda channel, with a view to distribute packages on my enterprise intranet. I may as well use that library `moirai` to test setting up a custom conda channel.

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

# Stocktake

The first impression is that there is not a clear, single path to standing up your own conda channel over HTTP(S), no turn-key solution. The closest may be the github repo [Private Conda Repository](https://github.com/DanielBok/private-conda-repo).

A first plan for the next steps, presumably next posts, are:

* First, set up a file based channel following the conda documentation for [creating custom channels](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/create-custom-channels.html).
* Second, try to use [PCR: Private Conda Repository](https://github.com/DanielBok/private-conda-repo).
