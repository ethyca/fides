from __future__ import annotations

import logging
import os
from numbers import Number
from typing import Any, Mapping, Union

MASKED = "MASKED"


class NotPii(str):
    """whitelist non pii data"""


def get_fides_log_record_factory() -> Any:
    """intercepts default LogRecord for custom handling of params"""

    def factory(  # pylint: disable=R0913
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: str,
        args: Union[tuple[Any, ...], Mapping[str, Any]],
        exc_info: Any,
        func: str = None,
        sinfo: str = None,
    ) -> logging.LogRecord:
        env_log_pii: bool = os.getenv("FIDESOPS__LOG_PII", "").lower() == "true"
        new_args = args
        if not env_log_pii and not name.startswith("uvicorn"):
            new_args = tuple(_mask_pii_for_logs(arg) for arg in args)
        return logging.LogRecord(
            name=name,
            level=level,
            pathname=fn,
            lineno=lno,
            msg=msg,
            args=new_args,
            exc_info=exc_info,
            func=func,
            sinfo=sinfo,
        )

    return factory


def _mask_pii_for_logs(parameter: Any) -> Any:
    """
    :param parameter: param that contains possible pii
    :return: depending on ENV config, returns masked pii param.

    Don't mask numeric values as this can throw errors in consumers
    format strings.
    """

    if isinstance(parameter, (NotPii, Number)):
        return parameter

    return MASKED


def _log_exception(exc: BaseException, dev_mode: bool = False) -> None:
    """If dev mode, log the entire traceback"""
    if dev_mode:
        logging.error(exc, exc_info=True)
    else:
        logging.error(exc)


def _log_warning(exc: BaseException, dev_mode: bool = False) -> None:
    """If dev mode, log the entire traceback"""
    if dev_mode:
        logging.warning(exc, exc_info=True)
    else:
        logging.warning(exc)
