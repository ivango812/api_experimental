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
                    # self.assertTrue(is_user_error(status_code))
                # try:
                #     func(*args_with_case)
                # except:
                #     print('Error in test: {}{}'.format(func.__name__, case))
                #     raise
        return wrapper
    return decorator