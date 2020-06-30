# pdbr

[Rich](https://github.com/willmcgugan/rich) is a great library for terminal output. In order to make the PDB results more colorful.

## Installing

Install with `pip` or your favorite PyPi package manager.

```
pip install pdbr
```

## Breakpoint

In order to use ```breakpoint()```, set **PYTHONBREAKPOINT** with "pdbr.set_trace"

```python
import os

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"
```

or just import pdbr

```python
import pdbr
```

## Traceback
In order to use Rich's traceback, set **USE_RICH_TRACEBACK** as True.

```python
import pdbr

os.environ["USE_RICH_TRACEBACK"] = "True"

# use PYGMENTS_THEME env to change theme of traceback.
os.environ["PYGMENTS_THEME"] = "monokai"
```

## Samples
### The difference from PDB
![](/samples/sample1.png)

### Style sample
![](/samples/sample2.png)

### Traceback
![](/samples/sample3.png)
