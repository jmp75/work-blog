---
title: "Upgrading a C++ streamflow compilation toolchain"
description: Moving a legacy Visual C++ 13 toolchain to something newer 
comments: true
hide: false
toc: true
layout: post
hide: false
categories: [recipes, VCPP, C++]
image: https://docs.conda.io/en/latest/_images/conda_logo.svg
author: "<a href='https://github.com/jmp75'>J-M</a>"
# permalink: /codespaces
---

# Background

For years I've been contributing to and maintaining, at work, a [software stack for streamflow forecasting](https://github.com/csiro-hydroinformatics/streamflow-forecasting-tools-onboard/). It is a stack with a core in C++. For a variety of reasons (licencing, habits, inertia) it is still compiled with the microsoft VCPP2013 toolchain. The most recent versions of some of the third party dependencies are starting to not be compiling with fthat 10 year old compiler, making maintenance more difficult.

This is not a particularly popular topic, but I am posting to at least organise and plan a migration.

# Current status

On Windows, we are relying on vcxproj files. A fair bit of work went into being able to manage switching configurations more easily than via horrendous hard coded paths, which is the baffling default behavior with these files, or at least, was. The supposedly "user-friendly" GUIs to manage project settings foster an unholly mess unless users are on a very tight leash. The Readme at [vcpp-commons](https://github.com/jmp75/vcpp-commons) includes instructions on how to set things up, and how to use it from visual c++ project files.

There are tools in the microsoft ecosystem to manage dependencies and configurations that were not existing 10 years ago. Here [is one, Conan](https://blog.conan.io/2021/02/10/Dependencies-Visual-Studio-C++-property-files.html), essentially doing what I put in place 10 years ago. There is also [vcpkg](https://vcpkg.io/en/index.html) which I looked at a few years back. Be it as it may, we have a legacy that worked for a while, so we are likely to keep using it.

We are using property files (.props files) to manage centrally some definitions, so that our vcxproj files look like:

```xml
  <ImportGroup Label="PropertySheets">
    <Import Project="$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props" Condition="exists('$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props')" Label="LocalAppDataPlatform" />
    <Import Project="$(UserProfile)/vcpp_config.props" Condition="exists('$(UserProfile)/vcpp_config.props')" />
  </ImportGroup>
  <PropertyGroup>
    <IncludePath>../include;$(LocalIncludePaths);$(IncludePath)</IncludePath>
    <ReferencePath>$(VisualLeakDetectorLibPath);$(LocalLibraryPaths);$(ReferencePath)</ReferencePath>
    <LibraryPath>$(VisualLeakDetectorLibPath);$(LocalLibraryPaths);$(LibraryPath)</LibraryPath>
  </PropertyGroup>
  <ItemDefinitionGroup>
    <Link>
      <AdditionalLibraryDirectories>$(LocalLibraryPaths);%(AdditionalLibraryDirectories)</AdditionalLibraryDirectories>
      <AdditionalDependencies>netcdf.lib;yaml-cpp.lib;moirai.lib;%(AdditionalDependencies)</AdditionalDependencies>
      <!--AdditionalDependencies>vld.lib;%(AdditionalDependencies)</AdditionalDependencies-->
    </Link>
  </ItemDefinitionGroup>
```

A priori this is independent of the version of compiler used. A priori.

```xml
<PlatformToolset>v120</PlatformToolset>
```

So, is it just a matter of just bulk replacing to `<PlatformToolset>v143</PlatformToolset>`? Even if considering only the purely mechanistic aspect (notwithstanding users), probably not.

## Dependencies

the following figure gives an overview of the dependencies of the main DLLs. There are already several versions of the MS C runtimes, which is possible so long as libraries interact in a binary compatible way (C API). Usually, C++ level binary compatibility is not achievable. Never, in practice, so far as I recall.

![]({{ site.baseurl }}/images/swift-library-dependencies-win.png  "swift-library-dependencies-windows")

# High level options

* Give up on compiling using MS VCpp and use the MinGW toolchain
* Upgrade the compilation to a newer

* netcdf: does this need to be stuck to msvcr100.dll (not that it is much of a problem)
* boost: while boost is largely header only, it has a few libraries. These need to be brought to the same version of VCPP.

* Move to use `cmake` to manage compilations, exactly as we do on Linux.
* Set up a CI/CD for compilation on windows.
* Automation of the migration to various versions of MSVCPP.

# Plan

Mibrate to 2017 (vcpp v14.x)

# Log

I already have visual studio installed.

Install ms build tools for visual studio 2017

https://www.boost.org/doc/libs/1_79_0/more/getting_started/windows.html

** Visual Studio 2017 Developer Command Prompt v15.0

c:\src\tmp>7z x boost_1_79_0.7z

seventy odd thousands of files, so it takes a fair bit of time.

```text
Building Boost.Build engine
LOCALAPPDATA=C:\Users\per202\AppData\Local
Found with vswhere C:\Program Files\Microsoft Visual Studio\2022\Professional
Found with vswhere C:\Program Files\Microsoft Visual Studio\2022\Professional
###
### Using 'vc143' toolset.
###
```

```bat
mkdir c:\tmp\boost
b2.exe  --prefix=c:\tmp\boost
```

```text
c:/src/tmp/boost_1_79_0/tools/build/src/build\targets.jam:617: in start-building from module targets
error: Recursion in main target references
error: the following target are being built currently:
error: ./forward -> ./stage -> ./stage-proper -> ***libs/filesystem/build/stage*** -> libs/filesystem/build/stage-dependencies -> libs/log/build/stage -> libs/log/build/stage-dependencies -> ***libs/filesystem/build/stage***
```

Go for the prebuilt windows binaries then...



https://www.boost.org/users/download/

https://sourceforge.net/projects/boost/files/boost-binaries/1.79.0/boost_1_79_0-msvc-14.1-64.exe/download


```bat
set vcpp_ver=14.1
set boost_ver=1_79_0
set vcpp_ver_s=141

set src_root_dir=C:\local\boost_%boost_ver%
set src_lib_dir=%src_root_dir%\lib64-msvc-%vcpp_ver%
set src_header_dir=%src_root_dir%\boost

set dest_root_dir=C:\local
set dest_dbg_root_dir=C:\localdev
set dest_lib_dir=%dest_root_dir%\libs\64
set dest_dbg_lib_dir=%dest_dbg_root_dir%\libs\64
set dest_header_dir=%dest_root_dir%\include
:: Cleanup or backup?

mkdir %dest_lib_dir%

set COPYOPTIONS=/Y /R /D

xcopy %src_lib_dir%\boost_chrono-vc%vcpp_ver_s%* %dest_lib_dir%\  %COPYOPTIONS%
xcopy %src_lib_dir%\boost_date_time-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\boost_filesystem-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\boost_system-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\boost_thread-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\boost_regex-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%

xcopy %src_lib_dir%\libboost_chrono-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\libboost_date_time-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\libboost_filesystem-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\libboost_system-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\libboost_thread-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%
xcopy %src_lib_dir%\libboost_regex-vc%vcpp_ver_s%* %dest_lib_dir%\ %COPYOPTIONS%

mkdir %dest_header_dir%
mv %src_header_dir% %dest_header_dir%\
```

Try to compile moirai with later vcpp. 

Open project with msvstudio 2022. Offers to upgrade the win sdk to a couple of versions. Am wary of not using the very latest 10.0.19xxxx which may be too recent. Choosing 10.0.17763.0. Platform toolset to v141

```xml
    <WindowsTargetPlatformVersion>10.0.17763.0</WindowsTargetPlatformVersion>
    <PlatformToolset>v141</PlatformToolset>
```

Compiles.


netCDF

https://docs.unidata.ucar.edu/netcdf-c/current/winbin.html  appears vcpp 2017. 
https://downloads.unidata.ucar.edu/netcdf-c/4.9.0/netCDF4.9.0-NC4-64.exe

It appears to run on top of v140 platform tools. OK. Try. May see if we can compile from source with v141 target.

```bat
xcopy C:\tmp\netcdf\bin\*.dll %dest_lib_dir%\ %COPYOPTIONS%
xcopy C:\tmp\netcdf\lib\*.lib %dest_lib_dir%\ %COPYOPTIONS%

mkdir %dest_header_dir%\netcdf
xcopy C:\tmp\netcdf\include\*.h %dest_header_dir%\netcdf\ %COPYOPTIONS%
```

jsoncpp

Getting my fork, concise-project file. 

```xml
    <PlatformToolset>v141</PlatformToolset>
    <WindowsTargetPlatformVersion>10.0.17763.0</WindowsTargetPlatformVersion>
```

Does the trick. Note that without `WindowsTargetPlatformVersion` in the project file, this failed to compile.

Now, how do I automate the building of these? TODO perhaps streamline the powershell script to deal with jsoncpp too. Even if likely very infrequent.

```bat
set jsoncpp_srcdir=C:\src\jsoncpp
set jsoncpp_builddir=%jsoncpp_srcdir%\makefiles\custom\x64
xcopy %jsoncpp_builddir%\Release\jsoncpp.dll %dest_lib_dir%\ %COPYOPTIONS%
xcopy %jsoncpp_builddir%\Release\jsoncpp.lib %dest_lib_dir%\ %COPYOPTIONS%
:: Debug also needed, likely. Know of very odd crashes when mixing debug/nondebug in the past. May not be the case anymore. 

mkdir %dest_dbg_lib_dir%
xcopy %jsoncpp_builddir%\Debug\jsoncpp.dll %dest_dbg_lib_dir%\ %COPYOPTIONS%
xcopy %jsoncpp_builddir%\Debug\jsoncpp.lib %dest_dbg_lib_dir%\ %COPYOPTIONS%
xcopy %jsoncpp_builddir%\Debug\jsoncpp.pdb %dest_dbg_lib_dir%\ %COPYOPTIONS%

set robocopy_opt=/MIR /MT:1 /R:2 /NJS /NJH /NFL /NDL /XX
robocopy %jsoncpp_srcdir%\include\json %dest_header_dir%\json  %robocopy_opt%
```

```bat
set yamlcpp_srcdir=C:\src\yaml-cpp
set yamlcpp_builddir=%yamlcpp_srcdir%\vsproj\x64
xcopy %yamlcpp_builddir%\Release\yaml-cpp.dll %dest_lib_dir%\ %COPYOPTIONS%
xcopy %yamlcpp_builddir%\Release\yaml-cpp.lib %dest_lib_dir%\ %COPYOPTIONS%
:: Debug also needed, likely. Know of very odd crashes when mixing debug/nondebug in the past. May not be the case anymore. 
xcopy %yamlcpp_builddir%\Debug\yaml-cpp.dll %dest_dbg_lib_dir%\ %COPYOPTIONS%
xcopy %yamlcpp_builddir%\Debug\yaml-cpp.lib %dest_dbg_lib_dir%\ %COPYOPTIONS%
xcopy %yamlcpp_builddir%\Debug\yaml-cpp.pdb %dest_dbg_lib_dir%\ %COPYOPTIONS%

robocopy %yamlcpp_srcdir%\include\yaml-cpp %dest_header_dir%\yaml-cpp  %robocopy_opt%
```

Now on to datatypes. All good. 

deploylocal.ps from here on, normally. 

Note: was expecting catch.hpp to be missing. But no. So, are the tests not compiling? may be disabled in the solution. 

```bat
robocopy C:\src\config-utils\catch\include\catch %dest_header_dir%\catch  %robocopy_opt%
```


# Market review

`moirai` grew out of specific projects almost a decade ago, but its inception did not occur without looking first at third party options. There were surprisingly few I could identify, and of the ones I saw licensing or design made it difficult to adopt as they were. Still, in 2022 is there, on conda-forge or not, something making `moirai` possibly redundant?

It can be tricky to find relevant work without a time consuming research. A cursory scan comes up:

* [Cppy](https://anaconda.org/conda-forge/cppy) seems to have intersects, but this is solely Python-centric.
* [Loki-lib](https://github.com/vancegroup-mirrors/loki-lib) is an (underappreciated) library with reference counting features, but not on conda-forge. I believe Loki-lib was largely written by [Andrei Alexandrescu](https://erdani.org/index.html), author of [Modern C++ Design](http://amazon.com/exec/obidos/ASIN/0201704315/modecdesi-20), one of the most impressive computer science book I read.

Maybe there is a place for `moirai`. Plus the name is not taken...


# Walkthrough

I already forked and cloned staged-recipes from the previous post. 

```sh
cd ~/src/staged-recipes
git checkout main
git branch moirai
```

## Starting point

[`grayskull`](https://github.com/conda-incubator/grayskull#introduction) is userful to generate meta.yaml stubs out of python packages, and not applicable in this case.

I learned the hard way that installing conda-build, grayskull and shyaml and `conda update conda`in my conda base environment landed me in a broken mamba and incompatible package versions. So, this time create a new dedicate environment:

```sh
conda create -n cf python=3.9 mamba -c conda-forge
conda activate cf
mamba install -c conda-forge conda-build grayskull # grayskull not for this post, but other future submissions
```

Is there an example I can start from and work by inference and similarity rather than first principles?

[libnetcdf-feedstock](https://github.com/conda-forge/libnetcdf-feedstock/blob/main/recipe/meta.yaml) may be an appropriate case to start from, even if more sophisticated than my case. Rather than strip down this libnetcdf recipe though, I work from the example in the staged-recipe and add, staying closer to [contributing packages](https://conda-forge.org/docs/maintainer/adding_pkgs.html)

I did bump into a couple of issues, but I got less issues than I thought to get a package compiling

The end result should be something like:

<!-- NOTE: we need to use a 'raw' section; ninja2 things otherwise mess things up at rendering with Jekyll 
https://stackoverflow.com/questions/52324134/getting-an-liquid-exception-liquid-syntax-error-while-using-jekyll
-->

{% highlight yaml %}
{% raw %}

{% set name = "moirai" %}
{% set version = "1.1" %}

package:
  name: {{ name|lower }}
  version: {{ version }}

source:
  # url: https://github.com/moirai/moirai/releases/download/{{ version }}/moirai-{{ version }}.tar.gz
  # and otherwise fall back to archive:
  url: https://github.com/csiro-hydroinformatics/moirai/archive/refs/tags/{{ version }}.tar.gz
  sha256: b329353aee261ec42ddd57b7bb4ca5462186b2d132cdb2c9dacc9325899b85f3

build:
  number: 0

requirements:
  build:
    - cmake
    - make  # [not win]
    # - pkg-config  # [not win]
    # - gnuconfig  # [unix]
    - {{ compiler('c') }}
    - {{ compiler('cxx') }}
  run:
    - curl # [win]
    - libgcc # [unix]

test:
  files:
    - CMakeLists.txt
  commands:
    - ls

about:
  home: https://github.com/csiro-hydroinformatics/moirai
  summary: 'Manage C++ objects lifetime when exposed through a C API'
  description: |
    This C++ library is designed to help handling C++ objects from so called opaque pointers, via a C API, featuring:
      * counting references via the C API to C++ domain objects
      * handle C++ class inheritance even via opaque pointers
      * mechanism for resilience to incorrect type casts
      * thread-safe design
  license: BSD-3-Clause
  license_family: BSD
  license_file: LICENSE.txt
  doc_url: https://github.com/csiro-hydroinformatics/moirai/blob/master/doc/Walkthrough.md
  dev_url: https://github.com/csiro-hydroinformatics/moirai

extra:
  recipe-maintainers:
    - jmp75

{% endraw %}
{% endhighlight %}

Note that you do need `make` as a build requirement besides `cmake`, otherwise you'd end up with :

```text
CMake Error: CMake was unable to find a build program corresponding to "Unix Makefiles".  CMAKE_MAKE_PROGRAM is not set.  You probably need to select a different build tool.
CMake Error: CMAKE_C_COMPILER not set, after EnableLanguage
CMake Error: CMAKE_CXX_COMPILER not set, after EnableLanguage
```

build.sh:

```sh
#!/bin/bash
# Build moirai.

mkdir -v -p build
cd build

# May be needed for unit tests down the track?
export TERM=
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib

# cmake -DCMAKE_CXX_COMPILER=g++ -DCMAKE_C_COMPILER=gcc -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_PREFIX_PATH=/usr/local -DCMAKE_MODULE_PATH=/usr/local/share/cmake/Modules/ -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON ..
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=${PREFIX} -DBUILD_SHARED_LIBS=ON ../
make -j 2 install
# rm -rf ../build/ # not if we want to run the unit tests
```

## Building locally on linux64

Note: although it may have changed by the time you read this, at the time I write I may have to `export DOCKER_IMAGE=quay.io/condaforge/linux-anvil-cos7-x86_64` to force that image being used. See [previous post](https://jmp75.github.io/work-blog/recipes/conda/conda-forge/2022/06/04/conda-packages-conda-forge.html).

```sh
conda activate cf
export DOCKER_IMAGE=quay.io/condaforge/linux-anvil-cos7-x86_64

cd ~/src/staged-recipes
python ./build-locally.py linux64
```

and the build seems OK...

```text
+ touch /home/conda/staged-recipes/build_artifacts/conda-forge-build-done
```

## Building locally on win64

Trying to run build-locally.py with the option win64 returns: `ValueError: only Linux/macOS configs currently supported, got win64`

You'll want to read or re-read the conda-forge documentation [Using cmake](https://conda-forge.org/docs/maintainer/knowledge_base.html?#using-cmake) and [particularities on windows](https://conda-forge.org/docs/maintainer/knowledge_base.html?#particularities-on-windows)

Trying for `bld.bat`:

```bat
REM Build moirai.
@REM Credits: some material in this file are courtesy of Kavid Kent (ex Australian Bureau of Meteorology)

mkdir build
cd build

@REM following may be unncessary
set PATH="%PREFIX%\bin";%PATH%

:: Configure using the CMakeFiles
cmake -G "%CMAKE_GENERATOR%" ^
      -DCMAKE_INSTALL_PREFIX:PATH="%LIBRARY_PREFIX%" ^
      -DCMAKE_PREFIX_PATH:PATH="%LIBRARY_PREFIX%" ^
      -DCMAKE_BUILD_TYPE:STRING=Release ^
      ..

if %errorlevel% neq 0 exit 1
msbuild /p:Configuration=Release /v:q /clp:/v:q "INSTALL.vcxproj"
if %errorlevel% neq 0 exit 1
@REM del *.*
```

Since the local build script cannot emulate a win64 build, I am trying to set up on a Windows box and see what a `conda build` gives.

I first tried on my Windows desktop where I do have vs 2019 and 2022 installed. Not sure whether they can be used. [This section of the conda-forge doc](https://conda-forge.org/docs/maintainer/knowledge_base.html?highlight=compiler%20cxx#local-testing) seem to suggest Microsoft Build Tools for Visual Studio 2017 is required, but the link to the Python wiki page on Windows compilers is covering many more versions, so this is rather confusing. See the Appendix for more details on what happens in this case.

Trying again on a windows machine, but installing visual studio build tools 2017.

After creating the conda environment `cf`, similar to the above on Linux:

```bat
cd c:\src\staged-recipes\recipes
conda build moirai
```

"mostly" works. for a minute or two it seems to freeze at a "number of files" line:

```text
Packaging moirai
INFO:conda_build.build:Packaging moirai
Packaging moirai-1.1-h82bb817_0
INFO:conda_build.build:Packaging moirai-1.1-h82bb817_0
number of files: 11
```

then:

```text
PGO: UNKNOWN is not implemented yet!
PGO: UNKNOWN is not implemented yet!
Unknown format
Unknown format
Unknown format
Unknown format
   INFO: sysroot: 'C:/Windows/' files: '['zh-CN/winhlp32.exe.mui', 'zh-CN/twain_32.dll.mui', 'zh-CN/regedit.exe.mui', 'zh-CN/notepad.exe.mui']'

<edit: snip>

Importing conda-verify failed.  Please be sure to test your packages.  conda install conda-verify to make this message go away.
```

`conda search -c conda-forge conda-verify` indeed returns something. Noted...

```text
<edit: snip>

## Package Plan ##

  environment location: C:\Users\xxxyyy\Miniconda3\envs\cf\conda-bld\moirai_1654825059872\_test_env


The following NEW packages will be INSTALLED:

    ca-certificates: 2022.4.26-haa95532_0
    curl:            7.82.0-h2bbff1b_0
    libcurl:         7.82.0-h86230a5_0
    libssh2:         1.10.0-hcd4344a_0
    moirai:          1.1-h82bb817_0         local
    openssl:         1.1.1o-h2bbff1b_0
    vc:              14.2-h21ff451_1
    vs2015_runtime:  14.27.29016-h5e58377_2
    zlib:            1.2.12-h8cc25b3_2
```

```text
<edit: snip>

set PREFIX=C:\Users\xxxyyy\Miniconda3\envs\cf\conda-bld\moirai_1654825059872\_test_env
set SRC_DIR=C:\Users\xxxyyy\Miniconda3\envs\cf\conda-bld\moirai_1654825059872\test_tmp
(cf) %SRC_DIR%>call "%SRC_DIR%\conda_test_env_vars.bat"
(cf) %SRC_DIR%>set "CONDA_SHLVL="   &&
(cf) %SRC_DIR%>conda activate "%PREFIX%"
(%PREFIX%) %SRC_DIR%>IF 0 NEQ 0 exit /B 1
(%PREFIX%) %SRC_DIR%>call "%SRC_DIR%\run_test.bat"
(%PREFIX%) %SRC_DIR%>ls
(%PREFIX%) %SRC_DIR%>IF -1073741511 NEQ 0 exit /B 1
```

The latter fails because the command line `ls` borks with the error message (windows box error message) `ls.exe - Entry Point not found`. `where ls` returns `C:\Users\xxxyyy\Miniconda3\envs\cf\Library\usr\bin\ls.exe` so this is something that came from conda.

Taking a look at the resulting `moirai-1.1-h82bb817_0.tar.bz2` file, the content looks sensible (include header files, bin/moirai.dll)

```text
info/hash_input.json
info/index.json
info/files
info/paths.json
info/about.json
info/git
info/recipe/build.sh
info/recipe/meta.yaml.template
info/licenses/LICENSE.txt
Library/include/moirai/extern_c_api_as_opaque.h
Library/include/moirai/extern_c_api_as_transparent.h
Library/include/moirai/setup_modifiers.h
Library/include/moirai/reference_handle_map_export.h
Library/include/moirai/error_reporting.h
Library/include/moirai/reference_handle.h
info/recipe/conda_build_config.yaml
info/recipe/meta.yaml
info/test/run_test.bat
info/recipe/bld.bat
Library/bin/moirai.dll
Library/include/moirai/reference_handle_test_helper.hpp
Library/include/moirai/opaque_pointers.hpp
Library/include/moirai/reference_type_converters.hpp
Library/include/moirai/reference_handle.hpp
```

# Recapitulation and summary

In some respects I had less issues with this conda package than the "pure python" one, partly because of prior experience, but not entirely.

I may be in a decent place to submit this to the conda-forge/staged-recipe repository. I may hold off a bit though. First, the unit tests in moirai are not exercised by the meta.yaml file (or build scripts). Second, I may next look at setting up a conda channel to test managing conda dependencies, even if I see `moirai` as belonging to conda-forge rather than a private channel. Third, there are probably other things I need to tidy up.

To recapitulate on the essentials out of post:

```sh
conda create -n cf python=3.9 mamba -c conda-forge
conda activate cf
# grayskull not for this post, but other future submissions
mamba install -c conda-forge conda-build conda-verify grayskull 
```

The draft conda recipe for `moirai` at this stage is available [there](https://github.com/jmp75/staged-recipes/tree/a4c0e075230699b7f4dfd86e91f8f6b4ebca9af8/recipes/moirai)

# Acknowledgements

Some of the conda recipe trialled was influenced by prior work by Kavid Kent (ex Australian Bureau of Meteorology).

# Appendices

## Appendix: if missing ms build tools 2017

If trying without having installed ms build tools 2017:

```text
%SRC_DIR%>CALL %BUILD_PREFIX%\etc\conda\activate.d\vs2017_get_vsinstall_dir.bat
Did not find VSINSTALLDIR
Windows SDK version found as: "10.0.19041.0"
The system cannot find the path specified.
Did not find VSINSTALLDIR
CMake Error at CMakeLists.txt:16 (PROJECT):
  Generator

    Visual Studio 15 2017 Win64

could not find any instance of Visual Studio.
```

```text
(cf) %SRC_DIR%>set "SCRIPTS=%PREFIX%\Scripts"
(cf) %SRC_DIR%>set "LIBRARY_PREFIX=%PREFIX%\Library"
(cf) %SRC_DIR%>set "LIBRARY_BIN=%PREFIX%\Library\bin"
(cf) %SRC_DIR%>set "LIBRARY_INC=%PREFIX%\Library\include"
(cf) %SRC_DIR%>set "LIBRARY_LIB=%PREFIX%\Library\lib"

(cf) %SRC_DIR%>set "c_compiler=vs2017"
(cf) %SRC_DIR%>set "fortran_compiler=gfortran"
(cf) %SRC_DIR%>set "vc=14"
(cf) %SRC_DIR%>set "cxx_compiler=vs2017"
```


call C:\Users\xxxyyy\Miniconda3\Scripts\activate.bat

Note:
```
base                  *  C:\Users\xxxyyy\Miniconda3\envs\cf
                         C:\Users\xxxyyy\Miniconda3\envs\cf\conda-bld\moirai_1654760072022\_build_env
                         C:\Users\xxxyyy\Miniconda3\envs\cf\conda-bld\moirai_1654760072022\_h_env
```


If I try to start with Visual Studio 2022 Developer Command Prompt v17.1.5. Then conda environment activation, still:

```
%SRC_DIR%>CALL %BUILD_PREFIX%\etc\conda\activate.d\vs2017_get_vsinstall_dir.bat
Did not find VSINSTALLDIR
Windows SDK version found as: "10.0.19041.0"
**********************************************************************
** Visual Studio 2022 Developer Command Prompt v17.1.5
** Copyright (c) 2022 Microsoft Corporation
**********************************************************************
[ERROR:vcvars.bat] Toolset directory for version '14.16' was not found.
[ERROR:VsDevCmd.bat] *** VsDevCmd.bat encountered errors. Environment may be incomplete and/or incorrect. ***
[ERROR:VsDevCmd.bat] In an uninitialized command prompt, please 'set VSCMD_DEBUG=[value]' and then re-run
[ERROR:VsDevCmd.bat] vsdevcmd.bat [args] for additional details.
[ERROR:VsDevCmd.bat] Where [value] is:
[ERROR:VsDevCmd.bat]    1 : basic debug logging
[ERROR:VsDevCmd.bat]    2 : detailed debug logging
[ERROR:VsDevCmd.bat]    3 : trace level logging. Redirection of output to a file when using this level is recommended.
[ERROR:VsDevCmd.bat] Example: set VSCMD_DEBUG=3
[ERROR:VsDevCmd.bat]          vsdevcmd.bat > vsdevcmd.trace.txt 2>&1
Did not find VSINSTALLDIR
CMake Error at CMakeLists.txt:16 (PROJECT):
  Generator

    Visual Studio 15 2017 Win64

  could not find any instance of Visual Studio.
-- Configuring incomplete, errors occurred!
```

## Resources

* [Reference Counting in Library Design – Optionally and with Union-Find Optimization](https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.85.6335&rep=rep1&type=pdf)
