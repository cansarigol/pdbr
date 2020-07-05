def foo():
    import pdbr; pdbr.set_trace()
    raise Exception()

if __name__ == "__main__":
    foo()