import functools


def cases(cases):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args):
            for case in cases:
                if not isinstance(case, tuple):
                    case = (case,)
                args_with_case = (self,) + args + case
                with self.subTest(case=case):
                    func(*args_with_case)
        return wrapper
    return decorator