from rich.layout import Layout


def set_history_file(filename):
    import atexit
    import os
    import readline

    histfile = os.path.join(os.path.expanduser("~"), filename)
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)


def make_layout():
    layout = Layout()
    left_layout = Layout(name="left", ratio=2)
    right_layout = Layout(name="right")
    layout.split(left_layout, right_layout, direction="horizontal")
    return layout


def set_traceback(theme):
    from rich.traceback import install

    install(theme=theme)
