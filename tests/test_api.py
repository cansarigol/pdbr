import pdbr


def test_api_attr():
    assert pdbr.__all__ == [
        "set_trace",
        "run",
        "pm",
        "post_mortem",
        "celery_set_trace",
        "RichPdb",
        "pdbr_context",
    ]
