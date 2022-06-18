
"I always like things to be automated, so that I can always redo it, because I always assume my first effort is going to be crap, and it always is. And normally my second and third are crap as well."

Jeremy Howard



https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html

https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/create-custom-channels.html

https://www.fast.ai/2021/07/15/fastconda/  https://github.com/fastai/fastconda   has some elements of pipelines but may be geared towards anaconda hosted channels. Not sure I can repurpose.


Maybe upfront: https://conda-forge.org/docs/

https://conda-forge.org/docs/user/ci-skeleton.html

https://github.com/conda-forge/astra-toolbox-feedstock is a recently accepted recipe. Likely a good template to study fopr the swift stack.

give a bo to conda smithy. The [conda forge documentation](https://conda-forge.org/docs/user/ci-skeleton.html#) actually rather confused me. The github [readme of conda-smithy](https://github.com/conda-forge/conda-smithy) may be better.


```sh
mamba install -c conda-forge conda-smithy
```


`conda smithy --help`
usage: conda smithy [-h] [--version] {init,register-github,register-ci,azure-buildid,regenerate,rerender,recipe-lint,ci-skeleton,update-cb3,generate-feedstock-token,register-feedstock-token,update-anaconda-token,rotate-anaconda-token,update-binstar-token,rotate-binstar-token} ...



```sh
mkdir -p ~/src/tmp/refcount/recipe
cd ~/src/tmp/refcount/recipe
curl -o meta.yaml https://raw.githubusercontent.com/jmp75/staged-recipes/refcount/recipes/refcount/meta.yaml

git config --global init.defaultBranch main

cd ~/src/tmp/
conda smithy init ./refcount/recipe/

conda smithy register-github --organization csiro-hydroinformatics ./refcount-feedstock
```

```text
RuntimeError: No github token. Go to https://github.com/settings/tokens/new and generate
a token with repo access. Put it in ~/.conda-smithy/github.token
```

7 days.
repo: Full control of private repositories 

```sh
cd ~/src/tmp
conda smithy register-github --organization csiro-hydroinformatics ./refcount-feedstock
```


```text
No numpy version specified in conda_build_config.yaml.  Falling back to default numpy value of 1.16
WARNING:conda_build.metadata:No numpy version specified in conda_build_config.yaml.  Falling back to default numpy value of 1.16
Adding in variants from internal_defaults
INFO:conda_build.variants:Adding in variants from internal_defaults
Created csiro-hydroinformatics/refcount-feedstock on github

Repository registered at github, now call 'conda smithy register-ci'
```

register a CI. Azure. Odd documentation.

For Azure, you will have to create a service connection with the same name as your github user or org https://dev.azure.com/YOUR_ORG/feedstock-builds/_settings/adminservices 

Can create csiro-hydroinformatics organisation

https://dev.azure.com/csiro-hydroinformatics/feedstock-builds/_settings/adminservices indeed then works out. But what from here on??? "New service connection" GitHub connection I presume?

create a feedstock-builds azure project ??

captured images:

```text
ls ../work-blog/images/
conda-smithy-001.png  conda-smithy-003.png  conda-smithy-005.png  ettrema-waters-light.png  logo.png                                try_climb_back.jpg
conda-smithy-002.png  conda-smithy-004.png  copied_from_nb        favicon.ico               refcount-conda-forge-pr-submission.png
```

```sh
export AZURE_ORG_OR_USER=csiro-hydroinformatics

conda smithy register-ci \
  --organization csiro-hydroinformatics \
  --feedstock_directory ./refcount-feedstock \
  --without-travis \
  --without-circle \
  --without-appveyor \
  --without-drone \
  --without-webservice \
  --without-anaconda-token
```

```text
No circle token.  Create a token at https://circleci.com/account/api and
put it in ~/.conda-smithy/circle.token
No appveyor token. Create a token at https://ci.appveyor.com/api-token and
Put one in ~/.conda-smithy/appveyor.token
No drone token. Create a token at https://cloud.drone.io/account and
Put one in ~/.conda-smithy/drone.token
No anaconda token. Create a token via
  anaconda auth --create --name conda-smithy --scopes "repos conda api"
and put it in ~/.conda-smithy/anaconda.token
No numpy version specified in conda_build_config.yaml.  Falling back to default numpy value of 1.16
WARNING:conda_build.metadata:No numpy version specified in conda_build_config.yaml.  Falling back to default numpy value of 1.16
Adding in variants from internal_defaults
INFO:conda_build.variants:Adding in variants from internal_defaults
CI Summary for csiro-hydroinformatics/refcount-feedstock (can take ~30s):
Warning: By not registering an Anaconda/Binstar tokenyour feedstock CI may not be able to upload packagesto anaconda.org by default. It is recommended to set`upload_packages: False` per provider field inconda-forge.yml to disable package uploads.
Travis registration disabled.
Circle registration disabled.
No azure token. Create a token and
put it in ~/.conda-smithy/azure.token
No azure token. Create a token at https://dev.azure.com/conda-forge/_usersSettings/tokens and
put it in ~/.conda-smithy/azure.token
/home/per202/miniconda/envs/cf/lib/python3.9/site-packages/conda_smithy/azure_ci_utils.py:74: UserWarning: No token available.  No modifications will be possible!
  warnings.warn(
```

https://dev.azure.com/csiro-hydroinformatics/_usersSettings/tokens

image 006

try again:


vsts.exceptions.VstsAuthenticationError: The requested resource requires user authentication: https://dev.azure.com/csiro-hydroinformatics/feedstock-builds/_apis/serviceendpoint/endpoints?type=GitHub

I suppose this is still progress. Still hard not to scream.

I maybe should have started with https://medium.com/@lgouarin/conda-smithy-an-easy-way-to-build-and-deploy-your-conda-packages-12216058648f

