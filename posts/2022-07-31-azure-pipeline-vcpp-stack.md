---
aliases:
- /C++/Debian/Python packaging/R packaging/VCPP/Windows/recipes/2022/07/31/azure-pipeline-vcpp-stack
author: <a href='https://github.com/jmp75'>J-M</a>
categories:
- recipes
- VCPP
- C++
- Debian
- Windows
- Python packaging
- R packaging
date: '2022-07-31'
description: Azure devops pipeline for a software stack with c++, Python and R packages
  across multiple repositories.
draft: false
layout: post
title: Azure devops CI pipeline for hydrologic forecasting software
toc: true

---

![Azure pipeline run](images/azure/pipeline_hydrofc.png "Azure pipeline run")

# Background

For years I've been contributing to and maintaining, at work, a [software stack for streamflow forecasting](https://github.com/csiro-hydroinformatics/streamflow-forecasting-tools-onboard/). Recently I explored [updating the compilation to a more recent Microsoft visual c++ compiler](https://jmp75.github.io/work-blog/recipes/vcpp/c++/2022/06/26/vcpp-compilation-upgrade.html) in another post.

This post is an overview of the process to set up a build pipeline on Azure Devops. Given the fairly complicated codebase dealt with, quite a few technical aspects will be touched on, but not in great details for the sake of keeping it a blog post rather than a full report.

# Pipeline inputs and outputs

## Outputs

* Debian packages for installing C++ pre-compiled libraries and header files
* Windows DLLs of these C++ pre-compiled libraries, compiled with Microsoft Visual C++ 2019.
* Python wheels of packages accessing these C++ libraries
* R packages accessing these C++ libraries. Source tarballs for Linux, and binary packages for Windows
* Matlab functions accessing these C++ libraries

Conda packages are an option for later - see appendix.

The outputs of this/these pipelines is used for installation as described for instance in [these instructions](https://github.com/csiro-hydroinformatics/streamflow-forecasting-tools-onboard/blob/master/doc/install_windows.md)

## Inputs

These C++, Python and R packages are in the following source code repositories.

* Third party libraries: boost libraries, netcdf, yaml-cpp and jsoncpp, threadpool, Catch headers.
  * [Boost C++](https://boost.org)
  * [netCDF4](https://www.unidata.ucar.edu/software/netcdf)
  * [yaml-cpp](https://github.com/csiro-hydroinformatics/yaml-cpp)
  * [jsoncpp](https://github.com/csiro-hydroinformatics/jsoncpp)
  * [threadpool](https://github.com/csiro-hydroinformatics/threadpool)
* Open source repositories with generic capabilities:
  * [rcpp-interop-commons](https://github.com/csiro-hydroinformatics/rcpp-interop-commons): supporting C API interoperability with Python, R, etc.
  * [moirai](https://github.com/csiro-hydroinformatics/moirai): Manage C++ Objects's lifetime when exposed through a C API
  * [pyrefcount](https://github.com/csiro-hydroinformatics/pyrefcount): Reference counting facilities for Python
  * [wila](https://github.com/csiro-hydroinformatics/wila): C++ header-only metaheuristics optimisation
  * [config-utils](https://github.com/csiro-hydroinformatics/config-utils)
  * [efts](https://github.com/csiro-hydroinformatics/efts)
  * [efts-python](https://github.com/csiro-hydroinformatics/efts-python)
  * [mhplot](https://github.com/csiro-hydroinformatics/mhplot): R visualisation for metaheuristics optimisation
  * [uchronia-time-series](https://github.com/csiro-hydroinformatics/uchronia-time-series):  time series handling for ensembles simulations and forecasts in C++
* Closed source, domain specific:
  * swift: Streamflow Water Information Forecasting Tools
  * FoGSS: A model for generated forecast guided stochastic scenarios of monthly streamflows out to 12 months
  * A repository with semi-automated build scripts

Another repository worth mentioning even if I do not envisage it being used is [c-api-wrapper-generation](https://github.com/csiro-hydroinformatics/c-api-wrapper-generation). It contains some fairly sophisticated capabilities for generating language bindings on top of C APIs. 

# Walkthrough

## Pipelines code repositories

A clone of the the azure devops pipelines described in this post are now mirrored at:

* [hydro-forecast-linux-pipeline](https://github.com/csiro-hydroinformatics/hydro-forecast-linux-pipeline)
* [hydro-forecast-windows-pipeline](https://github.com/csiro-hydroinformatics/hydro-forecast-windows-pipeline)

## Build platforms

For Linux I actually ended up building a Debian docker image on top of the `ubuntu-latest` image Azure Devops offers. This was partly an arbitrary choice (habits, and starting by reusing another pipeline).

For Windows, the [windows-2019](https://github.com/actions/virtual-environments/blob/main/images/win/Windows2019-Readme.md) image is more or less a given. Note that if I had chosen to, or had to, build with an older compiler version (for example, Python and conda on Windows I believe is at least recommending the 2017 toolchain currently), installing the Microsoft build toolchain would have been needed.

## Checking out source code

There is a description of how to [check out multiple repositories in your pipeline](https://docs.microsoft.com/en-us/azure/devops/pipelines/repos/multi-repo-checkout?view=azure-devops), which I may move to in the future but frankly felt cumbersome when I gave it a try, for that many repositories. Besides, I am starting from existing build scripts (bash or DOS) which I have an incentive to reuse.

Which brings us to dealing safely with checking out closed source code, requiring authentication.

### Using Personal Access Tokens (PAT)

**Disclaimer**: I believe the following recipe to be in line with best practices, but it is up to you to decide.

When googling for the documentation, [Use personal access tokens](https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate) tends to be what you land on, but this is more confusing than helpful. [Set secret variables](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops&tabs=yaml%2Cbatch#secret-variables) contains the key recipe to set up a secret PAT and pass it on to a pipeline task. Assuming you already have a PAT that you defined in a pipeline variable `SWIFT_PAT`, for which you checked `Keep this value secret`, you need to map this value to pass it to the script checking out source code:

```yaml
    - script: |
        call dos-setup.bat
        call checkout.bat
      env:
        SWIFT_PAT_ENV_VAR: $(SWIFT_PAT) # the recommended way to map to an env variable
        # NOTE: you cannot have the same name:
        # SWIFT_PAT: $(SWIFT_PAT) # <-- fails with a circular definition issue.
```

In your checkout.bat script you can retrieve `set MY_PAT=%SWIFT_PAT_ENV_VAR%` and use it as part of the URL portion e.g. `set MY_BITBUCKET_URL_ROOT=https://%YOUR_USERNAME%:%MY_PAT%@bitbucket.csiro.au/scm`

### A gotcha with Bitbucket PATs

if your closed source code is on Bitbucket, the bitbucket documentation [HTTP access tokens](https://confluence.atlassian.com/bitbucketserver/personal-access-tokens-939515499.html) is quite clear, but fails to document something. Bitbucket PAT generation tends to create them with slash characters "/" which is a special character for URLs so it [needs to be replace with "%2F"](https://stackoverflow.com/a/57732424/2752565) before you use it as a value for your Azure Pipeline, otherwise you end up with an invalid URL error when checking out. Note also that `%2` is fraught when used in DOS scripts, but if you use the recipe above, you should not come across an issue with this.

## Building C++ code

### Linux

Compilation on Linux is performed using `cmake`. The pipeline is not calling `cmake` and `make` commands directly, but building debian packages. One purpose of this build pipeline is to produce binary installable packages. It took me a fair bit of trial and error, two years ago, to find a suitable working recipe for Debian packaging of "my" libraries. There is documentation and plenty of examples out there, but plenty of variances in how it is done. An example can be found [in the Moirai repository](https://github.com/csiro-hydroinformatics/moirai/tree/experimental/debian), and the pipeline build commands are in [build_debian_pkgs.sh](https://github.com/csiro-hydroinformatics/hydro-forecast-linux-pipeline/blob/main/packages/build_debian_pkgs.sh).

### Windows

Compilation is done using microsoft visual c++ 2019, using visual studio solution files. Years ago, after enough frustrations invikig MSBuild.exe from DOS scripts, I moved to using powershell. Currently I am using the powershell [Invoke-MsBuild](https://github.com/deadlydog/Invoke-MsBuild) as a third party tool to invoke compilation, rather than mdsbuild.exe directly. This is a nifty basis to build my own powershell module (not open source yet), with `cmdlet`s such as:

```powershell
Install-SharedLibsMultiCfg -Solutions $lvlTwoSlns -LibsDirs $libsDirs -BuildPlatforms $buildPlatforms -BuildMode $buildMode -ToolsVersion $toolsVersion -LibNames $lvlTwoLibnames
```

which is roughly an equivalent of `make && make install` on Linux. The script for the step is [build-stack.ps1](https://github.com/csiro-hydroinformatics/hydro-forecast-windows-pipeline/blob/main/build-stack.ps1), and the bulk of the runtime in the pipeline.

## Unit tests

All C++ unit tests are run on the Windows platform. (Debian to follow soon). There are some lessons learnt in setting these up in a pipeline, but for now most of the code remains closed source and may be explored in another post.

## Python wheels, R package tarballs

The python package involved are "pure python" by design, and the wheels built are platform-agnostic and built only once on Linux ([build_python_pkgs.sh](https://github.com/csiro-hydroinformatics/hydro-forecast-linux-pipeline/blob/main/packages/build_python_pkgs.sh)). Most packages do deal a lot with interoperability with native libraries with a C API, but this is done via cffi as a runtime step.

R source packages can be built on either platform. Except R Windows binary packages, which are much preferable for Windows. [build_r_pkgs.sh](https://github.com/csiro-hydroinformatics/hydro-forecast-linux-pipeline/blob/main/packages/build_r_pkgs.sh) for the Linux pipeline builds these, also building tutorials ("vignettes") which are contributing to the testing regime, notably for the interoperability with the native libraries of the stack.

I decided not to build the R tarballs on Windows, but try instead to downloadm, from the Window pipeline, the last output resulting the Linux pipeline. Partly for the sake of gaining know-how. I ended up with way more confusion and frustration with this than I anticipated, as reflected in my [stackoverflow answer](https://stackoverflow.com/a/73136309/2752565) and [previous blog post](https://jmp75.github.io/work-blog/azure/devops/microsoft/2022/07/27/azure-devops-negative-experience.html).

Downloading the artifact from Windows is still done via a shell script [fetch-pkgs.sh](https://github.com/csiro-hydroinformatics/hydro-forecast-windows-pipeline/blob/main/fetch-pkgs.sh). The script is run mapping a `AZURE_DEVOPS_EXT_PAT` environment variable. The rather stunted [Sign in with a personal access token (PAT)](https://docs.microsoft.com/en-us/azure/devops/cli/log-in-via-pat) page somewhat explains why this is used.

### Bash on windows in Azure Pipelines: a gotcha with backslash directories

This is an occasion to point to an annoyance of backslashes as directory separators on Windows. I had defined a pipeline variable `linux_packages_dir: $(Build.ArtifactStagingDirectory)\swift_linux`, which would have been something like `D:\a\s\a\swift_linux`. In the script of a pipeline task `task: Bash@3`, if you use the variable evaluation `$(linux_packages_dir)` you loose the backslash separators. I had to rebuild the path and replace with forward slashes using the environment variable `BUILD_ARTIFACTSTAGINGDIRECTORY`, which is adding to the entropy.

```yaml
    inputs:
        targetType: 'inline'
        script: |
          # using $(linux_packages_dir) here fails; dir separators are lost.
          # linux_packages_dir=$(linux_packages_dir)
          # linux_packages_fwd_dir="${linux_packages_dir//\\//}"
          # instead have to do:
          linux_packages_fwd_dir="${BUILD_ARTIFACTSTAGINGDIRECTORY//\\//}/swift_linux"
          ./fetch-pkgs.sh ${linux_packages_fwd_dir}
      env:
        AZURE_DEVOPS_EXT_PAT: $(AZ_ARTIFACT_DL_PAT)
```

## Azure Artifacts

Outputs are published as collections of files in a "Universal Package". I have (had - may have changed) not found in the azure devops API way to query the artifacts for the version without downloading the whole artifact. A workaround is to publish two packages: a small one with the version number, and the real artifact.

To get a custom `$(Build.BuildNumber)`, and `r` is a counter reset to 1 every change of the major/minor versions, use `name: '0.1.$(Rev:r)'` on your pipeline. Then the publishing tasks can be:

```yaml
    - task: UniversalPackages@0
      displayName: Publish output bundle
      inputs:
        command: publish
        publishDirectory: '$(Build.ArtifactStagingDirectory)\release'
        vstsFeedPublish: 'my_project_name/hydro_forecast_win'
        vstsFeedPackagePublish: 'swift_win'
        versionOption: custom
        versionPublish: '$(Build.BuildNumber)'
        packagePublishDescription: 'Windows packages for swift and co.'

    - task: UniversalPackages@0
      displayName: Publish output bundle version
      inputs:
        command: publish
        publishDirectory: '$(Build.ArtifactStagingDirectory)\version'
        vstsFeedPublish: 'my_project_name/hydro_forecast_win'
        vstsFeedPackagePublish: 'swift_win_version'
        versionOption: custom
        versionPublish: '$(Build.BuildNumber)'
        packagePublishDescription: 'Version number for windows swift and co. bundle'

```

# Conclusion

While the level of overall build streamlining was always adequate for this software stack, previous pipelines run on Jenkins could not be maintained. Azure Devops appearing to be the main corporate standard, we've trialed setting up Azure pipelines. Despite some notable user frustrations with the Azure Devops environment, its peculiarities and access arrangements, this should have substantial dividends to expand the user base and enable new projects.

# Appendix

## Other possibilities

* I have explored using conda packaging to distribute the whole software stack. This appears feasible but is a leap I am not ready to do for several reasons (time, resources and confirmed user demands being the main ones). There is a substantial learning curve, technical and in terms of governance of a private conda channel.
* Caching some of the downloaded test data and third party libraries.
* Publishing a linux debian docker image ready to use as a baseline.

## Resources

URLs which may or may not have influenced this work:

* [Conda-forge default azure pipeline](https://github.com/conda-forge/staged-recipes/blob/main/.azure-pipelines/azure-pipelines-win.yml)
* [azure devops pipeline variables](https://docs.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops&tabs=yaml)
* [visual-studio-build-tools-2017-silent-install](https://silentinstallhq.com/visual-studio-build-tools-2017-silent-install-how-to-guide) may be handy if 2017 builds are needed e.g for conda.
* [Windows2019 image environment](https://github.com/actions/virtual-environments/blob/main/images/win/Windows2019-Readme.md)
* [Azure pipelines for Marian NMT](https://github.com/marian-nmt/marian-dev/blob/master/azure-pipelines.yml)
* [Trigger Build Task](https://marketplace.visualstudio.com/items?itemName=benjhuser.tfs-extensions-build-tasks)
