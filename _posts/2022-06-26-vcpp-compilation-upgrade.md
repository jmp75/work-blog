---
title: "Upgrading a C++ streamflow compilation toolchain"
description: Moving a legacy Visual C++ 13 toolchain to Build Tools 2017 
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

The following figure gives an overview of the dependencies of the main DLLs. There are already several versions of the MS C runtimes, which is possible so long as libraries interact in a binary compatible way (C API). Usually, C++ level binary compatibility is not achievable. Never, in practice, so far as I recall.

![]({{ site.baseurl }}/images/swift-library-dependencies-win.png  "swift-library-dependencies-windows")

# High level options

There are two main options to upgrade compilers

* Give up on compiling using MS VCpp and migrate the MinGW toolchain (gcc). While it would be interesting to trial, the debugging facilities offered by the Microsoft tools and IDEs are a key value added for users.
* Upgrade the compilation to a newer version of MS vc++. A quick scan of what is available out there for the dependencies of the stack (boost, netcdf, etc.) suggests that the build tool chain 2017 is prevalent.

Related to that are 2 key dependencies:

* netcdf: does this need to be stuck at msvcr100.dll (not that it is much of a problem)
* boost: while boost is largely header only, it has a few libraries. These need to be brought to the same version of VCPP as that to compile our software, contrary to netcdf, because boost is C++, not C.

Finally, some mostly orthogonal concerns

* Move to use `cmake` to manage compilations, exactly as we do on Linux.
* Set up a CI/CD for compilation on windows.
* Automation of the migration to various versions of MSVCPP.

# Plan

The rest of this post will be a log of a "dry run" trying to migrate to MS build toolchain 2017 (vcpp v14.x to be determined). I'll be capturing steps with a view to automate a CI/CD pipeline for windows soon, and also so that we can more easily adjust our target migration if I hit a blocker.

# Walkthrough

I already have a recent visual studio installed via my corporate software management system. I do need to install the Microsoft build tools for visual studio 2017. I note two things in what options this selects: the compiler version (perhaps known as platform version) is v141, and Windows SDK 10.0.17763.0.

## Boost

Read [Boost 1.79.0 for windows](https://www.boost.org/doc/libs/1_79_0/more/getting_started/windows.html). 

### Compile from source 

I first tried to compile from source, out of curiosity, but this failed. For the record a summary follows.

Opening the Visual Studio 2017 Developer Command Prompt v15.0, then `7z x boost_1_79_0.7z`. Note that running `bootstrap` indicated that it was `Using 'vc143' toolset` so this may be an issue.

Then doing:

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

### precompiled Boost binaries

[https://www.boost.org/users/download/](https://www.boost.org/users/download/) leads to [boost_1_79_0-msvc-14.1-64.exe on sourceforge](https://sourceforge.net/projects/boost/files/boost-binaries/1.79.0/boost_1_79_0-msvc-14.1-64.exe/download)

Copying a subset of the libraries:

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

if not exist %dest_lib_dir% mkdir %dest_lib_dir%

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

:: header files
mkdir %dest_header_dir%
move %src_header_dir% %dest_header_dir%\
```

## Moirai

[moirai](https://github.com/csiro-hydroinformatics/MOIRAI) is the workorse for reference counting opaque pointers.

Open project with ms vstudio 2019 or more does offer an upgrade of the project. There are options to upgrade the windows sdk to a couple of versions.including the 10.0.17763.0 we noted. Note that the Platform toolset option however **does not include v141**.

So, a manual modification of the .vcxproj file is needed (or via project properties from vsstudio after opening the project, it is available this time)

```xml
    <WindowsTargetPlatformVersion>10.0.17763.0</WindowsTargetPlatformVersion>
    <PlatformToolset>v141</PlatformToolset>
```

And this appears to compile.

## netCDF

Again may be interesting to compile from source, but not essential. [netcdf windows binaries document](https://docs.unidata.ucar.edu/netcdf-c/current/winbin.html). Appears to be compiled with vcpp 2017.

Downloading [netCDF4.9.0-NC4-64.exe](https://downloads.unidata.ucar.edu/netcdf-c/4.9.0/netCDF4.9.0-NC4-64.exe)

It appears to run on top of the v140 platform tools.That's OK since this is a C API. Try. May see if we can compile from source with v141 target later.

```bat
xcopy C:\tmp\netcdf\bin\*.dll %dest_lib_dir%\ %COPYOPTIONS%
xcopy C:\tmp\netcdf\lib\*.lib %dest_lib_dir%\ %COPYOPTIONS%

if not exist %dest_header_dir%\netcdf mkdir %dest_header_dir%\netcdf
xcopy C:\tmp\netcdf\include\*.h %dest_header_dir%\netcdf\ %COPYOPTIONS%
```

## jsoncpp

I have a [fork of jsoncpp and a branch](https://github.com/jmp75/jsoncpp/tree/custom/concise-project-file) with a customised .vcxproj file. Modifying with:

```xml
    <PlatformToolset>v141</PlatformToolset>
    <WindowsTargetPlatformVersion>10.0.17763.0</WindowsTargetPlatformVersion>
```

And this compiles fine. Note that without `WindowsTargetPlatformVersion` in the project file, this failed to compile.

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

## yaml-cpp

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

## uchronia / datatypes

[Uchronia - time series handling for ensembles simulations and forecasts in C++](https://github.com/csiro-hydroinformatics/uchronia-time-series) is the bedrock for data handling in our stack.

At this point I do need to copy the files for the catch unit testing framework, from [config-utils](https://github.com/csiro-hydroinformatics/config-utils), which the unit tests rely on. I notice also a bit of a minor issue, because the unit tests compile against the deployed headers, not the ones from source. This may be a gotcha to watch for, because my `vcpp_settings.props` file is not set up for development mode compilation. Beware when setting a build pipeline.

```bat
robocopy C:\src\config-utils\catch\include\catch %dest_header_dir%\catch  %robocopy_opt%
```

The compilation and deploymebnt of this is relatively streamlined by using a high level powershell script.

## swift

swift uses wila and its multithreading optimnisers. We need to install a complementary threadpool tool.

```bat
robocopy C:\src\threadpool\boost %dest_header_dir%\boost  %robocopy_opt%
```

Also uses in-house numerical header-only files:

```bat
robocopy C:\src\numerical-sl-cpp\algorithm\include\sfsl %dest_header_dir%\sfsl  %robocopy_opt%
robocopy C:\src\numerical-sl-cpp\math\include\sfsl %dest_header_dir%\sfsl  %robocopy_opt%
```

```text
Error	C2039	'tuple': is not a member of 'boost::math' (compiling source file channel_muskingum_nl.cpp)	libswift	c:\src\swift\libswift\include\swift\channel_muskingum_nl.h	74	
```

Seems I just an explicit additional `#include <boost/math/tools/tuple.hpp>` now with a more recent version of boost.

```bat
robocopy C:\local\include_old\tclap %dest_header_dir%\tclap  %robocopy_opt%
:: <!-- and for fogss later on: -->
robocopy C:\local\include_old\eigen3 %dest_header_dir%\eigen3  %robocopy_opt%
```

```text
Error	C2079	'outfile' uses undefined class 'std::basic_ofstream<char,std::char_traits<char>>'	swiftcl	c:\src\swift\applications\swiftcl\run_calibration.cpp	120	
```

`#include <fstream>` is now needed.

After that, unit tests are mostly as expected, a few watchpoint that may be red herring.

# Conclusion, and next

While it took a bit longer than ideal, so far, it looks rather straightforward and successful. Nothing was particularly risky a priori in this migration, but one is usually taken by a few surprises.

I am feeling the need for a more fully automated CI/CD. To be fair to myself, a fair bit of streamline already to build on. A challenge with the CI/CD, aside from some of the logistical cost of setting it up, probably on Azure Devops, is to define the artefacts it produces. Some artefacts the way they are currently would be better served as conda packages, but this is a larger scope.
