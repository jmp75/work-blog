---
title: "Compiling C++ libraries to WebAssembly - Part 1"
description: First attempt at compiling a streamflow forecasting software stack to WebAssembly
comments: true
hide: false
toc: true
layout: post
hide: false
categories: [C++, WASM, WebAssembly, emscripten, WASI]
# image: https://docs.conda.io/en/latest/_images/conda_logo.svg
author: "<a href='https://github.com/jmp75'>J-M</a>"
# permalink: /codespaces
---

<!-- <img src="https://github.com/carlosbaraza/web-assembly-logo/raw/master/dist/logo/web-assembly-logo.png"  width="25%" height="25%"  alt="eb-assembly-logo.png" class="center"> -->

!["web-assembly-logo.png 1"](https://github.com/carlosbaraza/web-assembly-logo/raw/master/dist/logo/web-assembly-logo.png "logo courtesy of https://github.com/carlosbaraza/web-assembly-logo")

# Introduction

Several previous posts are refering to a [software stack for streamflow forecasting](https://github.com/csiro-hydroinformatics/streamflow-forecasting-tools-onboard). The core of it is C++, and this is one of the primary target languages for [WebAssembly - WASM](https://webassembly.org/) to define a minimal viable product. I've been meaning for a while to acquaint myself a bit more with WebAssembly. While our forecasting software may be a big step to start with, it has the merit of being "real". This post will be an initial foray in targetting WASM: let's try and see.

# Waklthrough

Googling for starting examples, I somewhat arbitrarily ended up watching a bit of video [21 Compiling C/C++ to WebAssembly - Introduction to Google Colab for Research](https://www.youtube.com/watch?v=cewbhs9zq7A). That got me onto the [emscripten setup instructions](https://emscripten.org). Later on, I realised it may not be the only path, but I'll get back to that.

On Linux, the following worked just fine. There are Debian packages for emscripten, but the [emscripten setup instructions](https://emscripten.org) recommends the following.

```sh
git clone --depth=1 https://github.com/emscripten-core/emsdk.git
cd emsdk/
./emsdk install latest # takes a minute or so
./emsdk activate latest
source ./emsdk_env.sh
em++ --help # good, finds it
```

Going throught the [Emscripten Tutorial](https://emscripten.org/docs/getting_started/Tutorial.html), just the "hello world" part of it.

## Trying on one of my c++ codebase

The library [MOIRAI: Manage C++ Objects's lifetime when exposed through a C API](https://github.com/csiro-hydroinformatics/moirai) may be a natural starting point, as it is a workhorse for the C API of many larger libraries. It is small in size, but non-trivial, and the unit tests already feature techniques like C API with opaque pointers and template programming. It can be compiled using `cmake`.

Adapting [emscripten instructions for projects](https://emscripten.org/docs/compiling/Building-Projects.html#building-projects) to my case (where `emcmake $CM` below is `emcmake cmake -DBLAH_LOTS_OF_OPTIONS ..`, we'll get back to this)

```sh
cd ${GITHUB_REPOS}/moirai
mkdir -p embuild ; cd embuild
emcmake $CM
```

I get:

```text
CMake Error at /home/per202/src/emsdk/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake:136 (message):
  System LLVM compiler cannot be used to build with Emscripten! Check
  Emscripten's LLVM toolchain location in .emscripten configuration file, and
  make sure to point CMAKE_C_COMPILER to where emcc is located.  (was
  pointing to "gcc")
```

Googling for "System LLVM compiler cannot be used to build with Emscripten" was rather confusing me. My full expanded, failing command line looks like:

```sh
emcmake cmake -DCMAKE_CXX_COMPILER=g++ -DCMAKE_C_COMPILER=gcc -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_PREFIX_PATH=/usr/local -DCMAKE_MODULE_PATH=/usr/local/share/cmake/Modules/ -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON ..
```

Maybe removing most arguments?

```sh
emcmake cmake -DCMAKE_MODULE_PATH=/usr/local/share/cmake/Modules/ -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON ..
```

Nope, still not, same message. Well, how about trying to "point CMAKE_C_COMPILER to where emcc is located"?

```sh
emcmake cmake -DCMAKE_CXX_COMPILER=/home/per202/src/emsdk/upstream/emscripten/em++ -DCMAKE_C_COMPILER=/home/per202/src/emsdk/upstream/emscripten/emcc -DCMAKE_PREFIX_PATH=/usr/local -DCMAKE_MODULE_PATH=/usr/local/share/cmake/Modules/ -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON ..
```

Surprise, it works. Albeit with a warning.

```text
CMake Warning (dev) at CMakeLists.txt:145 (ADD_LIBRARY):
  ADD_LIBRARY called with SHARED option but the target platform does not
  support dynamic linking.  Building a STATIC library instead.  This may lead
  to problems.
```

Bring it on. Battle scarred. Let's plodder and see.

```sh
emmake make
```

results in:

```text
Scanning dependencies of target moirai
[  6%] Building CXX object CMakeFiles/moirai.dir/src/reference_handle.cpp.o
[ 12%] Building CXX object CMakeFiles/moirai.dir/src/reference_handle_map_export.cpp.o
[ 18%] Linking CXX static library libmoirai.a
[ 18%] Built target moirai
# etc. etc.
Scanning dependencies of target moirai_test_api
[ 81%] Building CXX object CMakeFiles/moirai_test_api.dir/tests/moirai_test_api/main.cpp.o
[ 87%] Linking CXX executable moirai_test_api.js
wasm-ld: error: duplicate symbol: free_string
>>> defined in libmoirai_test_lib_a.a(c_interop_api.cpp.o)
>>> defined in libmoirai_test_lib.a(c_interop_api.cpp.o)
```

Ok, not bad, really, compiling all the object files succeeds already. It is at linking stage that this falters, and given the above warning about shared/static libraries, fair enough.

# Taking stock

Our existing software stack is architectured for good reasons as a set of shared libraries (shared objects on Linux, "DLLs" on Windows). If `emscripten` does not support this, a significant reengineering may be on the card in order to target WASM.

But, really, shared libraries not supported? Google a bit.

I come across the [WebAssembly System Interface - WASI](https://wasi.dev/). Its documentation page [Writing WebAssembly - C/C++](https://docs.wasmtime.dev/wasm-c.html) and [LLVM - WebAssembly lld port](https://lld.llvm.org/WebAssembly.html) make me think that shared libraries. Noting that _flags related to dynamic linking, such `-shared` and `--export-dynamic` are not yet stable and are expected to change behavior in the future_.

## Other resources for next steps

* Very interested in [Porting libffi to pure WebAssembly](https://www.tweag.io/blog/2022-03-17-libffi-wasm32/), and also the company profile of the author.
* [minimal-cmake-emscripten-project](https://github.com/adevaykin/minimal-cmake-emscripten-project)
* [Compiling an Existing C Module to WebAssembly](https://developer.mozilla.org/en-US/docs/WebAssembly/existing_C_to_wasm)
* The Rust community seems to be quite actively interested in WASM
* [Bytecode Alliance](https://bytecodealliance.org/)
