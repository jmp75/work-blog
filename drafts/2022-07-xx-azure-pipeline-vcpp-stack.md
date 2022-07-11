---
title: "Azure devops pipeline for a c++ software stack"
description: Azure devops pipeline for a c++ software stack 
comments: true
hide: false
toc: true
layout: post
hide: false
categories: [recipes, VCPP, C++]
# image: https://docs.conda.io/en/latest/_images/conda_logo.svg
author: "<a href='https://github.com/jmp75'>J-M</a>"
# permalink: /codespaces
---

# Background

For years I've been contributing to and maintaining, at work, a [software stack for streamflow forecasting](https://github.com/csiro-hydroinformatics/streamflow-forecasting-tools-onboard/). Recently I explored [updating the compilation to a more recent Microsoft visual c++ compiler](https://jmp75.github.io/work-blog/recipes/vcpp/c++/2022/06/26/vcpp-compilation-upgrade.html) in another post.

This post is logging the process to set up a build pipeline on Azure Devops.

# Plan

Starting with the end in mind. I want to end up with the following artifacts:

* A zip archive of binaries and header files to deploy
* anything else?

The setup for checking out source code should be pretty similar to that already set up for bulding Linux artefacts. 

# Walkthrough

## Resources

Not really easy to locate a suitable recipe. I don't relish the prospect of building a yaml file from scratch 
https://github.com/conda-forge/staged-recipes/blob/main/.azure-pipelines/azure-pipelines-win.yml

maybe https://silentinstallhq.com/visual-studio-build-tools-2017-silent-install-how-to-guide/


