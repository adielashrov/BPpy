from copy import copy


def b_thread(func):
    def wrapper(*args):
        while True:
            m = None
            f = func(*args)
            while True:
                try:
                    e = f.send(m)
                    m = yield e
                    if m is None:
                        break
                except KeyError as ke:
                    print(f"Caught KeyError exception")
                    m = yield None
                    break
                except StopIteration as si:
                    print(f"Caught StopIteration exception")
                    m = yield None
                    break
    return wrapper

