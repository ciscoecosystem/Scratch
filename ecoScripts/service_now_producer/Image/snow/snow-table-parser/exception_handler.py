import inspect
import requests
from functools import wraps


def handle_exception(func):
    """
    handles the exception

    handles the exception of the passed function
    with proper message

    Parameters
    ----------
    func : function whose exception will be handled
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        err_msg = 'In function: {}, on line: {}. {}: {}'
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as err:
            raise requests.exceptions.HTTPError(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'HTTPError', err))
        except requests.exceptions.ConnectionError as err:
            raise requests.exceptions.ConnectionError(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'ConnectionError', err))
        except requests.exceptions.Timeout as err:
            raise requests.exceptions.Timeout(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'TimeoutError', err))
        except requests.exceptions.RequestException as err:
            raise requests.exceptions.RequestException(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'RequestError', err))
        except OSError as err:
            raise OSError(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'OSError', err))
        except IOError as err:
            raise IOError(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'IOError', err))
        except KeyError as err:
            raise KeyError(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'KeyError', err))
        except Exception as err:
            raise Exception(err_msg.format(
                inspect.trace()[-1][3], inspect.trace()[-1][2], 'Error', err))
    return wrapper
