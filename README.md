![splash](Source/splash.png)

This is the EPL-maintained version of the program originally written by Brad Buran.

[Help](https://EPL-Engineering.github.io/abr-peak-analysis/)

[Changelog](CHANGELOG.md)

Minimal Python environment:
```
conda create -n abr python=3.9.12
conda activate abr
conda install -c conda-forge nomkl numpy scipy matplotlib wxPython
conda install -c conda-forge numpy==2.0.2
conda install spyder
conda install pyinstaller
```

Notes: numpy v2.0.1 has bugs that break bundled apps without a console, e.g.:
```
  File "numpy\f2py\cfuncs.py", line 19, in <module>
    errmess = sys.stderr.write
AttributeError: 'NoneType' object has no attribute 'write'
```

See [here](https://github.com/numpy/numpy/issues/26862)
