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
        "apdbr_context",
        "install_log_capture",
        "uninstall_log_capture",
        "get_log_buffer",
        "CapturedLog",
        "collect_context",
        "render_whereami",
        "compute_diff",
        "render_diff",
        "DiffEntry",
        "register_pdbr_ipython_magics",
        "load_ipython_extension",
    ]
