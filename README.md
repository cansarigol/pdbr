# pdbr

[![PyPI version](https://badge.fury.io/py/pdbr.svg)](https://pypi.org/project/pdbr/) [![Python Version](https://img.shields.io/pypi/pyversions/pdbr.svg)](https://pypi.org/project/pdbr/) [![](https://github.com/cansarigol/pdbr/workflows/Release/badge.svg)](https://github.com/cansarigol/pdbr/actions?query=workflow%3ARelease) [![](https://github.com/cansarigol/pdbr/workflows/Test/badge.svg)](https://github.com/cansarigol/pdbr/actions?query=workflow%3ATest)

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

## New commands
### vars(v)
it is used to get the local variables list.

![](/images/image5.png)

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

## Vscode user snippet

To create or edit your own snippets, select **User Snippets** under **File > Preferences** (**Code > Preferences** on macOS), and then select **python.json**. Place the below snippet in json file.

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

## Samples
![](/images/image1.png)

![](/images/image3.png)

![](/images/image4.png)

### Traceback
![](/images/image2.png)
