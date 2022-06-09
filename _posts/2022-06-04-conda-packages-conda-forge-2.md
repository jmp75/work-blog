---
title: "Conda package for compiled native libraries"
description: Journey in building a conda package for C++ libraries
comments: true
hide: false
toc: false
layout: post
hide: false
categories: [recipes, conda, conda-forge, C++]
image: https://docs.conda.io/en/latest/_images/conda_logo.svg
author: "<a href='https://github.com/jmp75'>J-M</a>"
# permalink: /codespaces
---

# Background

I recently wrote about [submitting your first conda package to conda-forge](https://jmp75.github.io/work-blog/recipes/conda/conda-forge/2022/06/04/conda-packages-conda-forge.html). You'll find background on the "bigger picture" endeavour in that previous post.

This post is a follow-on with, perhaps, a second submission to conda-forge, this time not of a python package but a C++ library.

I'll try to package a relatively small C++ codebase [MOIRAI: Manage C++ objects lifetime when exposed through a C API](https://github.com/csiro-hydroinformatics/moirai). While dealing with very similar needs as refcount (reference counting and memory management), there is no explicit dependency between them.

# Market review

`moirai` grew out of specific projects almost a decade ago, but its inception did not occur without looking first at third party options. There were surprisingly few I could identify, and of the ones I saw licensing or design made it difficult to adopt as they were. Still, in 2022 is there, on conda-forge or not, something making `moirai` possibly redundant?

It can be tricky to find relevant work without a time consuming research. A cursory scan comes up:

* [Cppy](https://anaconda.org/conda-forge/cppy) seems to have intersects, but this is solely Python-centric.
* [Loki-lib](https://github.com/vancegroup-mirrors/loki-lib) is an (underappreciated) library with reference counting features, but not on conda-forge. I believe Loki-lib was largely written by [Andrei Alexandrescu](https://erdani.org/index.html), author of [Modern C++ Design](http://amazon.com/exec/obidos/ASIN/0201704315/modecdesi-20), one of the most impressive computer science book I read.

Maybe there is a place for `moirai`. Plus the name is not taken...

# Resources

* [Reference Counting in Library Design – Optionally and with Union-Find Optimization](https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.85.6335&rep=rep1&type=pdf)

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
mamba install -c conda-forge grayskull # not for this post, but other future submissions
mamba install -c conda-forge conda-build
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

and...

```text
+ touch /home/conda/staged-recipes/build_artifacts/conda-forge-build-done
```

## Building locally on win64?

https://conda-forge.org/docs/maintainer/knowledge_base.html?#using-cmake

https://conda-forge.org/docs/maintainer/knowledge_base.html?#particularities-on-windows

build.bat

```bat
cmake -G "%CMAKE_GENERATOR%" ^
      -DCMAKE_INSTALL_PREFIX:PATH="%LIBRARY_PREFIX%" ^
      -DCMAKE_PREFIX_PATH:PATH="%LIBRARY_PREFIX%" ^
      -DCMAKE_BUILD_TYPE:STRING=Release ^
      ..
```

python ./build-locally.py not unexpecdely:

ValueError: only Linux/macOS configs currently supported, got win64




I tried to `conda install -c conda-forge shyaml` which seems to be used by the scripts, but this did not alleviate the issue.

That took me some time to find a workaround to this one. The "exit status 1" is actually very misleading. The root cause is a `docker run -it` that exited with an error code 139. I seem to not be the only one to have bumped into [this issue](https://github.com/conda-forge/staged-recipes/issues/18127) still open. I may have pointed to the workaround in the conda-forge FAQ.

I needed to override the default docker image build-locally.py falls back to with:

```sh
python build-locally.py linux64
```

the build script works this time, but at some point:

```text
Processing $SRC_DIR
  Added file://$SRC_DIR to build tracker '/tmp/pip-build-tracker-bkn7ckr9'
  Running setup.py (path:$SRC_DIR/setup.py) egg_info for package from file://$SRC_DIR
  Created temporary directory: /tmp/pip-pip-egg-info-68li1y6t
  Preparing metadata (setup.py): started
  Running command python setup.py egg_info
  Traceback (most recent call last):
    File "<string>", line 2, in <module>
    File "<pip-setuptools-caller>", line 34, in <module>
    File "/home/conda/staged-recipes/build_artifacts/refcount_1654312313810/work/setup.py", line 41, in <module>
      with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    File "/home/conda/staged-recipes/build_artifacts/refcount_1654312313810/_h_env_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_placehold_pl/lib/python3.10/codecs.py", line 905, in open
      file = builtins.open(filename, mode, buffering)
  FileNotFoundError: [Errno 2] No such file or directory: '/home/conda/staged-recipes/build_artifacts/refcount_1654312313810/work/README.md'
  error: subprocess-exited-with-error
  
  × python setup.py egg_info did not run successfully.
  │ exit code: 1
  ╰─> See above for output.
  
  note: This error originates from a subprocess, and is likely not a problem with pip.

```

This is an issue that may be in my control.

```sh
cd ~/src/staged-recipes/build_artifacts/refcount_1654312313810/work
ls
## build_env_setup.sh  conda_build.sh  LICENSE.txt  MANIFEST.in  metadata_conda_debug.yaml  PKG-INFO  README.rst  refcount  refcount.egg-info  setup.cfg  setup.py
```

`refcount` has both a `README.md` and `README.rst`, the latter being an export from the former because pypi requires (or used to require) a README.rst to display correctly. The [zip archive of the source code on pypi](https://files.pythonhosted.org/packages/10/16/d143a863a79fb1f386bd78178257f6d0a3d085fd740ca94cb19af54a76c9/refcount-0.9.3.zip) indeed does not have the `README.md` file included.

I've inherited the practice to use in the packages `setup.py` the following, to limit redundances.

```python
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
    long_description_content_type='text/markdown'
```

Previously I needed to convert on the fly to restructured Text, but [Markdown is more supported](https://github.com/pypa/pypi-legacy/issues/148). Still there is a lot of inertia with restructuredText.

I may try to just nuke the README.rst. The only fly on the ointment is: is pypi ok with rendering markdown **correctly** these days? Probably; the [packaging documentation](https://packaging.python.org/en/latest/tutorials/packaging-projects/) is using README.md by default.

So, [build and submit](https://github.com/csiro-hydroinformatics/pyrefcount/blob/master/docs/tech_notes.md) to pypi the updated [refcount 0.9.4](https://pypi.org/project/refcount/0.9.4/) with no README.rst. Looks fine, including the zip source archive.

```text
RuntimeError: SHA256 mismatch: '21567918cb1bb30bf8116ce3483d3f431de202618eabbc6887b4814b40a3b94a' != 'bf8bfabdac6f0d9fe3734f1c1830fda8b9b2d740c90ecf8caf8c2ef3ed9c8442'
Traceback (most recent call last):
```

Right, I forgot to change the checksum in the meta.yaml file.

And... **it seems to complete**.

```text
import: 'refcount'
+ pip check
No broken requirements found.
+ exit 0

Resource usage statistics from testing refcount:
   Process count: 1
   CPU time: Sys=0:00:00.0, User=-
   Memory: 3.0M
   Disk usage: 28B
   Time elapsed: 0:00:02.1

TEST END: /home/conda/staged-recipes/build_artifacts/noarch/refcount-0.9.4-pyhd8ed1ab_0.tar.bz2
```

Submit the [pull request](https://github.com/conda-forge/staged-recipes/pull/19140), and pleasantly:

![refcount-conda-forge-pr-submission]({{ site.baseurl }}/images/refcount-conda-forge-pr-submission.png "refcount conda forge PR submission")

# Conclusion

While there were a couple of bumps along the way, this should end up with a positive outcome. If not with refcount on `conda-forge`, I've a better understanding to tackle conda packaging on the rest of the software stack.

* Building a conda package "from scratch" may not be the easiest learning path. Even if you indent to build a conda package not for conda-forge, going through the staged-recipes process may be a most
* Some of the reference documentation may need a spruice up. [Building conda packages from scratch](https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs.html) confused me. First, packaging a pypi package is not starting "from scratch" for most users. Second, inconsistencies in the documentation. I am sure I'll get back to that resource, but I wish there were more "water tight", step-by-step tutorials for conda packaging.
