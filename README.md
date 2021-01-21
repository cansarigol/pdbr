# pdbr

[![PyPI version](https://badge.fury.io/py/pdbr.svg)](https://pypi.org/project/pdbr/) [![Python Version](https://img.shields.io/pypi/pyversions/pdbr.svg)](https://pypi.org/project/pdbr/) [![](https://github.com/cansarigol/pdbr/workflows/Test/badge.svg)](https://github.com/cansarigol/pdbr/actions?query=workflow%3ATest)

pdbr is intended to make the PDB results more colorful. it uses [Rich](https://github.com/willmcgugan/rich) library to carry out that.


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

## New commands
### vars(v)
Get the local variables list as table.

### varstree(vt)
Get the local variables list as tree.

### inspect(i) / inspectall(ia)
[rich.inspect](https://rich.readthedocs.io/en/latest/introduction.html?s=03#rich-inspector)

![](/images/image5.png)

### pp
[rich.pretty.pprint](https://rich.readthedocs.io/en/latest/reference/pretty.html?highlight=pprint#rich.pretty.pprint)

## Config
### Style
In order to use Rich's traceback, style, and theme, set **setup.cfg**.

```
[pdbr]
style = yellow
use_traceback = True
theme = friendly
```

### History
**store_history** setting is used to keep and reload history, even the prompt is closed and opened again.
```
[pdbr]
...
store_history=.pdbr_history
```

### Celery
In order to use **Celery** remote debugger with pdbr, use ```celery_set_trace``` as below sample. For more information see the [Celery user guide](https://docs.celeryproject.org/en/stable/userguide/debugging.html).

```python
from celery import Celery

app = Celery('tasks', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    
    import pdbr; pdbr.celery_set_trace()
    
    return x + y

```

![](/images/image6.png)

## Vscode user snippet

To create or edit your own snippets, select **User Snippets** under **File > Preferences** (**Code > Preferences** on macOS), and then select **python.json**. 

Place the below snippet in json file for **pdbr**.

```
{
  ...
  "pdbr": {
        "prefix": "pdbr",
        "body": "import pdbr; pdbr.set_trace()",
        "description": "Code snippet for pdbr debug"
    },
}
```

For **Celery** debug.

```
{
  ...
  "rdbr": {
        "prefix": "rdbr",
        "body": "import pdbr; pdbr.celery_set_trace()",
        "description": "Code snippet for Celery pdbr debug"
    },
}
```

## Samples
![](/images/image1.png)

![](/images/image3.png)

![](/images/image4.png)

### Traceback
![](/images/image2.png)
