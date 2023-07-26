"""Utilities needed for creating the DSR Execution Graph."""
import traceback
from functools import wraps
from time import sleep
from typing import Any, Callable, Optional, Union

from loguru import logger

from fides.api.common_exceptions import (
    CollectionDisabled,
    NotSupportedForCollection,
    PrivacyRequestErasureEmailSendRequired,
    PrivacyRequestPaused,
    SkippingConsentPropagation,
)
from fides.api.models.privacy_request import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.util.consent_util import add_errored_system_status_for_consent_reporting
from fides.config import CONFIG


def retry(
    action_type: ActionType,
    default_return: Any,
) -> Callable:
    """
    Retry decorator for access and right to forget requests requests -

    If an exception is raised, we retry the function `count` times with exponential backoff. After the number of
    retries have expired, we call GraphTask.end() with the appropriate `action_type` and `default_return`.

    If we exceed the number of TASK_RETRY_COUNT retries, we re-raise the exception to stop execution of the privacy request.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def result(*args: Any, **kwargs: Any) -> Any:
            func_delay = CONFIG.execution.task_retry_delay
            method_name = func.__name__
            self = args[0]

            raised_ex: Optional[Union[BaseException, Exception]] = None
            for attempt in range(CONFIG.execution.task_retry_count + 1):
                try:
                    self.skip_if_disabled()
                    # Create ExecutionLog with status in_processing or retrying
                    if attempt:
                        self.log_retry(action_type)
                    else:
                        self.log_start(action_type)
                    # Run access or erasure request
                    return func(*args, **kwargs)
                except PrivacyRequestPaused as ex:
                    traceback.print_exc()
                    logger.warning(
                        "Privacy request {} paused {}",
                        method_name,
                        self.traversal_node.address,
                    )
                    self.log_paused(action_type, ex)
                    # Re-raise to stop privacy request execution on pause.
                    raise
                except PrivacyRequestErasureEmailSendRequired as exc:
                    traceback.print_exc()
                    self.log_end(action_type, ex=None, success_override_msg=exc)
                    self.resources.cache_erasure(
                        f"{self.traversal_node.address.value}", 0
                    )  # Cache that the erasure was performed in case we need to restart
                    return 0
                except (
                    CollectionDisabled,
                    NotSupportedForCollection,
                ) as exc:
                    traceback.print_exc()
                    logger.warning(
                        "Skipping collection {} for privacy_request: {}",
                        self.traversal_node.address,
                        self.resources.request.id,
                    )
                    self.log_skipped(action_type, exc)
                    return default_return
                except SkippingConsentPropagation as exc:
                    traceback.print_exc()
                    logger.warning(
                        "Skipping consent propagation on collection {} for privacy_request: {}",
                        self.traversal_node.address,
                        self.resources.request.id,
                    )
                    self.log_skipped(action_type, exc)
                    for pref in self.resources.request.privacy_preferences:
                        # For consent reporting, also caching the given system as skipped for all historical privacy preferences.
                        pref.cache_system_status(
                            self.resources.session,
                            self.connector.configuration.system_key,
                            ExecutionLogStatus.skipped,
                        )
                    return default_return
                except BaseException as ex:  # pylint: disable=W0703
                    traceback.print_exc()
                    func_delay *= CONFIG.execution.task_retry_backoff
                    logger.warning(
                        "Retrying {} {} in {} seconds...",
                        method_name,
                        self.traversal_node.address,
                        func_delay,
                    )
                    sleep(func_delay)
                    raised_ex = ex
            self.log_end(action_type, raised_ex)
            self.resources.request.cache_failed_checkpoint_details(
                step=action_type, collection=self.traversal_node.address
            )
            add_errored_system_status_for_consent_reporting(
                self.resources.session,
                self.resources.request,
                self.connector.configuration,
            )
            # Re-raise to stop privacy request execution on failure.
            raise raised_ex  # type: ignore

        return result

    return decorator
