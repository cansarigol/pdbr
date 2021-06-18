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
        right_body = Layout(name="right_body", ratio=1)

        layout.split(
            Layout(name="left_body", ratio=2),
            right_body,
            splitter="row",
        )

        right_body.split(
            Layout(name="up_footer", ratio=2), Layout(name="bottom_footer", ratio=1)
        )
        return layout

    def print(self, message, code, stack_trace, vars, **kwargs):
        try:
            self.layout["left_body"].update(code)
            self.layout["up_footer"].update(Panel(vars, title="Locals"))

            self.layout["bottom_footer"].update(
                Panel(Lines(stack_trace), title="Stack", style="white on blue")
            )

            self.console.print(self.layout, **kwargs)
            self.console.print(message, **kwargs)
        except NotRenderableError:
            self.console.print(message, **kwargs)
