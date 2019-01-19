import functools


def cases(cases):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args):
            for case in cases:
                if not isinstance(case, tuple):
                    case = (case,)
                args_with_case = args + case
                # func(*args_with_case)
                try:
                    func(*args_with_case)
                except:
                    print('Error in test: {}{}'.format(func.__name__, case))
                    raise
        return wrapper
    return decorator