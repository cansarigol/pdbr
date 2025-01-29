# pdbr

[![PyPI version](https://badge.fury.io/py/pdbr.svg)](https://pypi.org/project/pdbr/) [![Python Version](https://img.shields.io/pypi/pyversions/pdbr.svg)](https://pypi.org/project/pdbr/) [![](https://github.com/cansarigol/pdbr/workflows/Test/badge.svg)](https://github.com/cansarigol/pdbr/actions?query=workflow%3ATest) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/cansarigol/pdbr/master.svg)](https://results.pre-commit.ci/latest/github/cansarigol/pdbr/master)


`pdbr` is intended to make the PDB results more colorful. it uses [Rich](https://github.com/willmcgugan/rich) library to carry out that.


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
### (i)nspect / inspectall | ia
[rich.inspect](https://rich.readthedocs.io/en/latest/introduction.html?s=03#rich-inspector)
### search | src
Search a phrase in the current frame.
In order to repeat the last one, type **/** character as arg.
### sql
Display value in sql format. Don't forget to install [sqlparse](https://github.com/andialbrecht/sqlparse) package.
![](/images/image13.png)

It can be used for Django model queries as follows.
```
>>> sql str(Users.objects.all().query)
```
![](/images/image14.png)
### (syn)tax
[ val,lexer ] Display [lexer](https://pygments.org/docs/lexers/).
### (v)ars
Get the local variables list as table.
### varstree | vt
Get the local variables list as tree.

![](/images/image5.png)

## Config
Config is specified in **setup.cfg** and can be local or global. Local config (current working directory) has precedence over global (default) one. Global config must be located at `$XDG_CONFIG_HOME/pdbr/setup.cfg`.

### Style
In order to use Rich's traceback, style, and theme:

```
[pdbr]
style = yellow
use_traceback = True
theme = friendly
```

Also custom `Console` object can be assigned to the `set_trace`.
```python
import pdbr

from rich.console import Console
from rich.style import Style
from rich.theme import Theme

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
})
custom_style = Style(
    color="magenta",
    bgcolor="yellow",
    italic=True,
)
console = Console(theme=custom_theme, style=custom_style)

pdbr.set_trace(console=console)
```
### History
**store_history** setting is used to keep and reload history, even the prompt is closed and opened again:
```
[pdbr]
...
store_history=.pdbr_history
```

By default, history is stored globally in `~/.pdbr_history`.

### Context
The **context** setting is used to specify the number of lines of source code context to show when displaying stacktrace information.
```
[pdbr]
...
context=10
```
This setting is only available when using `pdbr` with `IPython`.

## Celery
In order to use **Celery** remote debugger with pdbr, use ```celery_set_trace``` as below sample. For more information see the [Celery user guide](https://docs.celeryproject.org/en/stable/userguide/debugging.html).

```python
from celery import Celery

app = Celery('tasks', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):

    import pdbr; pdbr.celery_set_trace()

    return x + y

```
#### Telnet
Instead of using `telnet` or `nc`, in terms of using pdbr style, `pdbr_telnet` command can be used.
![](/images/image6.png)

Also in order to activate history and be able to use arrow keys, install and use [rlwrap](https://github.com/hanslub42/rlwrap) package.

```
rlwrap -H '~/.pdbr_history' pdbr_telnet localhost 6899
```

## IPython

`pdbr` integrates with [IPython](https://ipython.readthedocs.io/).

This makes [`%magics`](https://ipython.readthedocs.io/en/stable/interactive/magics.html) available, for example:

```python
(Pdbr) %timeit range(100)
104 ns ± 2.05 ns per loop (mean ± std. dev. of 7 runs, 10,000,000 loops each)
```

To enable `IPython` features, install it separately, or like below:

```
pip install pdbr[ipython]
```

## pytest
In order to use `pdbr` with pytest `--pdb` flag, add `addopts` setting in your pytest.ini.

```
[pytest]
addopts: --pdbcls=pdbr:RichPdb
```

## sys.excepthook
The `sys.excepthook` is a Python system hook that provides a way to customize the behavior when an unhandled exception occurs. Since `pdbr` use  automatic traceback handler feature of `rich`, formatting exception print is not necessary if `pdbr` module is already imported.

In order to use post-mortem or perform other debugging features of `pdbr`,  override `sys.excepthook` with a function that will act as your custom excepthook:
```python
import sys
import pdbr

def custom_excepthook(exc_type, exc_value, exc_traceback):
    pdbr.post_mortem(exc_traceback, exc_value)

    # [Optional] call the original excepthook as well
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = custom_excepthook
```
Now, whenever an unhandled exception occurs, `pdbr` will be triggered, allowing you to debug the issue interactively.

## Context Decorator
`pdbr_context` and `apdbr_context` (`asyncio` corresponding) can be used as **with statement** or **decorator**. It calls `post_mortem` if `traceback` is not none.

```python
from pdbr import apdbr_context, pdbr_context

@pdbr_context()
def foo():
    ...

def bar():
    with pdbr_context():
        ...


@apdbr_context()
async def foo():
    ...

async def bar():
    async with apdbr_context():
        ...
```

![](/images/image12.png)
## Django DiscoverRunner
To being activated the pdb in Django test, change `TEST_RUNNER` like below. Unlike Django (since you are not allowed to use for smaller versions than 3), pdbr runner can be used for version 1.8 and subsequent versions.

```
TEST_RUNNER = "pdbr.runner.PdbrDiscoverRunner"
```
![](/images/image10.png)
## Middlewares
### Starlette
```python
from fastapi import FastAPI
from pdbr.middlewares.starlette import PdbrMiddleware

app = FastAPI()

app.add_middleware(PdbrMiddleware, debug=True)


@app.get("/")
async def main():
    1 / 0
    return {"message": "Hello World"}
```
### Django
In order to catch the problematic codes with post mortem, place the middleware class.

```
MIDDLEWARE = (
    ...
    "pdbr.middlewares.django.PdbrMiddleware",
)
```
![](/images/image11.png)
## Shell
Running `pdbr` command in terminal starts an `IPython` terminal app instance. Unlike default `TerminalInteractiveShell`, the new shell uses pdbr as debugger class instead of `ipdb`.
#### %debug magic sample
![](/images/image9.png)
### As a Script
If `pdbr` command is used with an argument, it is invoked as a script and [debugger-commands](https://docs.python.org/3/library/pdb.html#debugger-commands) can be used with it.
```python
# equivalent code: `python -m pdbr -c 'b 5' my_test.py`
pdbr -c 'b 5' my_test.py

>>> Breakpoint 1 at /my_test.py:5
> /my_test.py(3)<module>()
      1
      2
----> 3 def test():
      4         foo = "foo"
1     5         bar = "bar"

(Pdbr)

```
### Terminal
#### Django shell sample
![](/images/image7.png)

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
