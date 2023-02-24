blogging about the waa tool port from fortran.




quarto installed thanks to  apt
version 1.1.165

```sh
quarto create-project --type website:blog .
quarto install extension quarto-ext/video

cp -r $HOME/src/work-blog/_notebooks/* posts
cp -r $HOME/src/work-blog/_posts/* posts

cp $HOME/src/work-blog/images/* posts
cp -r $HOME/src/work-blog/images/copied_from_nb/* posts/

nbdev_migrate --path posts
```

```text
usage: nbdev_migrate [-h] [--fname FNAME] [--disp] [--stdin] [--no_skip]
nbdev_migrate: error: unrecognized arguments: -v
```

```
(bm) abcdef@keywest-bm:~/src/blog2$ conda list | grep nbdev
nbdev                     2.2.8                      py_0    fastai
```

`mamba update -c fastai -c conda-forge nbdev`

```
  - nbdev       2.2.8  py_0            fastai                       
  + nbdev       2.3.6  py_0            fastai/noarch            63kB
```