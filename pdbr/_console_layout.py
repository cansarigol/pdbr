from rich.containers import Lines
from rich.errors import NotRenderableError
from rich.layout import Layout
from rich.panel import Panel


class ConsoleLayoutMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class ConsoleLayout(metaclass=ConsoleLayoutMeta):
    def __init__(self, console):
        self.console = console
        self.layout = self._prep_layout()

    def _prep_layout(self):
        layout = Layout()
        body = Layout(name="body", ratio=2)
        footer = Layout(name="footer", ratio=1)
        layout.split(body, footer)

        body.split(
            Layout(name="left_body", ratio=2),
            Layout(name="right_body", ratio=1),
            splitter="row",
        )

        footer.split(
            Layout(name="left_footer"), Layout(name="right_footer"), splitter="row"
        )
        return layout

    def print(self, message, code, stack_trace, vars, **kwargs):
        try:
            self.layout["left_body"].update(message)
            self.layout["right_body"].update(code)
            self.layout["left_footer"].update(
                Panel(Lines(stack_trace), title="Stack", style="white on blue")
            )
            self.layout["right_footer"].update(Panel(vars, title="Locals"))

            self.console.print(self.layout, **kwargs)
        except NotRenderableError:
            self.console.print(message, **kwargs)
