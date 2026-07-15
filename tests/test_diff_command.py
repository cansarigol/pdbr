import dataclasses
import datetime
import inspect
import pdb
import uuid

import pytest

from pdbr._pdbr import rich_pdb_klass
from pdbr.diff_command import (
    ADDED,
    CHANGED,
    REMOVED,
    TYPE_CHANGED,
    compute_diff,
    render_diff,
    split_two_expressions,
)


@pytest.fixture
def RichPdb():
    currentframe = inspect.currentframe()

    def wrapper():
        rpdb = rich_pdb_klass(pdb.Pdb, show_layouts=False)()
        rpdb.botframe = currentframe.f_back
        rpdb.setup(currentframe.f_back, None)
        return rpdb

    return wrapper


class TestPrimitiveDiff:
    def test_equal_primitives_produce_no_changes(self):
        assert compute_diff(1, 1) == []
        assert compute_diff("hello", "hello") == []
        assert compute_diff(None, None) == []

    def test_changed_primitive_is_single_entry(self):
        changes = compute_diff(1, 2)

        assert len(changes) == 1
        assert changes[0].kind == CHANGED
        assert changes[0].old == 1
        assert changes[0].new == 2

    def test_none_vs_value_is_type_change(self):
        changes = compute_diff(None, 42)

        assert len(changes) == 1
        assert changes[0].kind == TYPE_CHANGED


class TestDictDiff:
    def test_changed_dict_value(self):
        changes = compute_diff({"amount": 100}, {"amount": 200})

        assert [(c.kind, c.old, c.new) for c in changes] == [
            (CHANGED, 100, 200),
        ]
        assert changes[0].path == (".amount",)

    def test_added_and_removed_keys_together(self):
        changes = compute_diff({"a": 1, "b": 2}, {"a": 1, "c": 3})

        kinds = {c.kind for c in changes}
        assert kinds == {ADDED, REMOVED}
        by_kind = {c.kind: c for c in changes}
        assert by_kind[REMOVED].old == 2
        assert by_kind[ADDED].new == 3

    def test_nested_dict_path_is_composed(self):
        changes = compute_diff({"user": {"name": "alice"}}, {"user": {"name": "bob"}})

        assert len(changes) == 1
        assert changes[0].path == (".user", ".name")

    def test_non_identifier_key_uses_index_notation(self):
        changes = compute_diff({"a b": 1}, {"a b": 2})

        assert changes[0].path == ("['a b']",)


class TestListDiff:
    def test_same_length_diff_per_index(self):
        changes = compute_diff([1, 2, 3], [1, 5, 3])

        assert [(c.kind, c.path, c.old, c.new) for c in changes] == [
            (CHANGED, ("[1]",), 2, 5),
        ]

    def test_longer_list_reports_removals_and_additions(self):
        removed_changes = compute_diff([1, 2, 3], [1])
        added_changes = compute_diff([1], [1, 2, 3])

        assert {c.kind for c in removed_changes} == {REMOVED}
        assert {c.kind for c in added_changes} == {ADDED}

    def test_tuple_normalises_like_list(self):
        changes = compute_diff((1, 2), (1, 3))

        assert changes[0].kind == CHANGED


class TestSetDiff:
    def test_added_and_removed_elements(self):
        changes = compute_diff({1, 2, 3}, {2, 3, 4})

        kinds = {c.kind for c in changes}
        assert kinds == {ADDED, REMOVED}
        assert {c.new for c in changes if c.kind == ADDED} == {4}
        assert {c.old for c in changes if c.kind == REMOVED} == {1}


class TestTypeChange:
    def test_dict_vs_list_is_type_changed(self):
        changes = compute_diff({"a": 1}, [1])

        assert len(changes) == 1
        assert changes[0].kind == TYPE_CHANGED

    def test_int_vs_str_is_type_changed(self):
        changes = compute_diff(1, "1")

        assert changes[0].kind == TYPE_CHANGED


class TestDataclassNormalization:
    @dataclasses.dataclass
    class Sample:
        name: str
        count: int
        tags: list

    def test_changed_field(self):
        a = self.Sample(name="a", count=1, tags=["x"])
        b = self.Sample(name="a", count=2, tags=["x"])

        changes = compute_diff(a, b)

        assert len(changes) == 1
        assert changes[0].path == (".count",)
        assert (changes[0].old, changes[0].new) == (1, 2)

    def test_nested_list_field_is_walked(self):
        a = self.Sample(name="a", count=1, tags=["x", "y"])
        b = self.Sample(name="a", count=1, tags=["x", "z"])

        changes = compute_diff(a, b)

        assert changes[0].path == (".tags", "[1]")
        assert changes[0].kind == CHANGED


class TestGenericObjectFallback:
    class Bag:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def test_vars_used_for_generic_class(self):
        a = self.Bag(x=1, y=2)
        b = self.Bag(x=1, y=99)

        changes = compute_diff(a, b)

        assert len(changes) == 1
        assert changes[0].path == (".y",)


class TestLeafTypes:
    def test_datetimes_compared_as_leaves(self):
        a = datetime.datetime(2026, 7, 14, 10, 0)
        b = datetime.datetime(2026, 7, 14, 11, 0)

        changes = compute_diff(a, b)

        assert len(changes) == 1
        assert changes[0].kind == CHANGED

    def test_uuid_compared_as_leaf(self):
        u1 = uuid.uuid4()
        u2 = uuid.uuid4()

        changes = compute_diff({"id": u1}, {"id": u2})

        assert changes[0].kind == CHANGED


class TestCycleAndDepthGuards:
    def test_self_referential_dict_does_not_recurse_forever(self):
        a = {}
        a["self"] = a
        b = {}
        b["self"] = b

        assert compute_diff(a, b) == []

    def test_depth_limit_falls_back_to_equality(self):
        deep_a = {"n": {"n": {"n": {"n": 1}}}}
        deep_b = {"n": {"n": {"n": {"n": 2}}}}

        changes = compute_diff(deep_a, deep_b, max_depth=1)

        assert len(changes) == 1
        assert changes[0].kind == CHANGED


class TestRenderDiff:
    def test_no_changes_produces_placeholder(self):
        from rich.text import Text

        rendered = render_diff([])

        assert isinstance(rendered, Text)
        assert "no differences" in rendered.plain

    def test_rendered_table_contains_paths_and_values(self):
        from rich.console import Console

        changes = compute_diff(
            {"amount": 100, "status": "draft", "extra": True},
            {"amount": 200, "status": "sent", "new_key": 5},
        )
        console = Console(record=True, width=120)
        console.print(render_diff(changes, before_label="before", after_label="after"))
        output = console.export_text()

        assert "Diff" in output
        assert "amount" in output
        assert "100" in output and "200" in output
        assert "status" in output
        assert "(missing)" in output
        assert "(removed)" in output

    def test_type_change_row_marks_types(self):
        from rich.console import Console

        changes = compute_diff({"a": 1}, {"a": "1"})
        console = Console(record=True, width=120)
        console.print(render_diff(changes))
        output = console.export_text()

        assert "int" in output
        assert "str" in output


class TestSplitTwoExpressions:
    def test_simple_split(self):
        assert split_two_expressions("a b") == ("a", "b")

    def test_returns_none_on_single_token(self):
        assert split_two_expressions("just_one") is None

    def test_respects_parentheses(self):
        assert split_two_expressions("foo(1, 2) bar[0]") == (
            "foo(1, 2)",
            "bar[0]",
        )

    def test_respects_string_literals(self):
        assert split_two_expressions("'a b' 'c d'") == ("'a b'", "'c d'")

    def test_empty_string_returns_none(self):
        assert split_two_expressions("") is None


class TestDoDiffCommand:
    def test_do_diff_prints_table(self, capsys, RichPdb):
        rpdb = RichPdb()
        rpdb.curframe.f_locals["before"] = {"amount": 100}
        rpdb.curframe.f_locals["after"] = {"amount": 200}

        rpdb.do_diff("before after")

        output = capsys.readouterr().out
        assert "Diff" in output
        assert "amount" in output
        assert "100" in output
        assert "200" in output

    def test_do_diff_no_args_reports_usage(self, capsys, RichPdb):
        RichPdb().do_diff("")

        assert "Usage: diff" in capsys.readouterr().out

    def test_do_diff_bad_expression_shows_error(self, capsys, RichPdb):
        RichPdb().do_diff("undefined_a undefined_b")

        output = capsys.readouterr().out
        assert "NameError" in output or "undefined" in output.lower()


class TestIPythonMagic:
    def test_diff_magic_registers_and_stores_last_diff(self):
        pytest.importorskip("IPython")
        from IPython.testing.globalipapp import get_ipython

        from pdbr.ipython_magics import register_pdbr_ipython_magics

        ip = get_ipython()
        assert register_pdbr_ipython_magics(ip) is True

        ip.user_ns["before"] = {"amount": 100}
        ip.user_ns["after"] = {"amount": 200, "extra": 1}

        ip.run_line_magic("diff", "before after")

        assert "_last_diff" in ip.user_ns
        changes = ip.user_ns["_last_diff"]
        kinds = {c.kind for c in changes}
        assert CHANGED in kinds
        assert ADDED in kinds
