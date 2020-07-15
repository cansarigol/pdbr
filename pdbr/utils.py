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


def set_traceback(theme):
    from rich.traceback import install

    install(theme=theme)
