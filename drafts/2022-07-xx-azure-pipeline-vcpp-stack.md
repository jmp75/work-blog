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

https://docs.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops&tabs=yaml

maybe https://silentinstallhq.com/visual-studio-build-tools-2017-silent-install-how-to-guide/  Nah, actually just morve to 2019 toolchain.

https://github.com/actions/virtual-environments/blob/main/images/win/Windows2019-Readme.md

https://github.com/marian-nmt/marian-dev/blob/master/azure-pipelines.yml


Building the R tarballs on a Linux (easier, perhaps). How do I download them in another pipeline to build on windows?

[Trigger Build Task](https://marketplace.visualstudio.com/items?itemName=benjhuser.tfs-extensions-build-tasks)

## Getting a pipeline to work

Reusing swift_pat as per what was set up for Debian build
Bitbucket - User "Manage Account" - Personal access tokens - permissions are read projects and read repositories. Note that the key will be readonly once at creation. You may want to save it to a secure location.

https://confluence.atlassian.com/bitbucketserver/personal-access-tokens-939515499.html

https://docs.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops&tabs=yaml%2Cbatch#secret-variables

### Third party precompiled data

```bat
curl -o libs_third_party.7z https://cloudstor.aarnet.edu.au/plus/s/GdV0QmFISDHrwPG/download
```
Idea: is it possible to use J Lerat's caching?

## Troubleshooting

```
{"@t":"2022-07-26T10:22:42.4886223Z","@m":"An error occurred on the service. User '9fa77fd6-2efe-46ec-b780-0a181276deff' lacks permission to complete this action. You need to have 'AddPackage'.","@i":"1f83248f","@l":"Error","SourceContext":"ArtifactTool.Program","UtcTimestamp":"2022-07-26 10:22:42.488Z"}
```

Comparing with another pipeline that works:
Project Collection Build Service (blahblah) is not present with a contributor Role

Also more to read.
https://stackoverflow.com/questions/58780741/azure-devops-user-lacks-permission-to-complete-this-action-you-need-to-have-a

https://stackoverflow.com/questions/57154296/azure-devops-publishing-to-own-feed-suddenly-results-in-403-forbidden

https://stackoverflow.com/questions/71206808/setting-azure-build-permissions-to-push-to-shared-feed

Add to confusion: my employer provides setup where the organisation and the project use the same name. Our proOD222236-DigWaterAndLandscapes

Looking for "..." buttons to access settings, which appear no longer available. 

