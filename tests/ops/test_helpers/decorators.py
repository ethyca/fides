import functools
import os


def override_envvars(env_vars):
    """
    Decorator to override environment variables for the duration of a test.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            original_env_vars = {}
            for key, value in env_vars.items():
                if key in os.environ:
                    original_env_vars[key] = os.environ.get(key)
                os.environ[key] = value
            try:
                return func(*args, **kwargs)
            finally:
                for key in env_vars.keys():
                    if key in original_env_vars:
                        os.environ[key] = original_env_vars[key]
                    else:
                        os.environ.pop(key, None)

        return wrapper

    return decorator
