# src/_robot/actions/fb_create_account.py
from typing import List, Union, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator
from src.my_types import (
    BrowserTaskType,
    BrowserWorkerSignals,
    CreateAccountPayloadType,
)
import sys, traceback

MIN = 60_000


def fb_create_account(
    page: Page,
    task: BrowserTaskType,
    settings: dict,
    signals: BrowserWorkerSignals,
    stage: Optional[int] = None,
) -> Union[bool, str]:
    task.action_payload = CreateAccountPayloadType(task.action_payload)
    log_prefix = f"[Task {task.user_info.username} - fb_create_account]"
    progress: List[int] = [0, 4]  # current, total

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])
        print(f"{log_prefix} Progress: {progress[0]}/{progress[1]} - {message}")

    try:
        # if settings.get("phone")
        # stage 1: Opening registration page
        try:
            emit_progress_update("Opening registration page...")
            page.goto("https://m.facebook.com/reg", timeout=MIN)
            emit_progress_update("Page loaded.")
        except PlaywrightTimeoutError as e:
            emit_progress_update(f"ERROR: Timeout while navigating to URL.")
            print(
                f"{log_prefix} ERROR: Timeout when navigating to URL: {e}",
                file=sys.stderr,
            )
            if settings.get("raw_proxy"):
                signals.proxy_not_ready_signal.emit(task, settings.get("raw_proxy"))
            return False
        except Exception as e:
            if "ERR_PROXY_NOT_READY" == str(e) or "ERR_TIMED_OUT" in str(e):
                raise e
            if "ERR_ABORTED" in str(e):
                pass  # This is often an expected error when closing the browser.
            else:
                emit_progress_update(
                    f"ERROR: An unexpected error occurred during navigation."
                )
                print(
                    f"{log_prefix} ERROR: An unexpected error occurred during navigation: {e}",
                    file=sys.stderr,
                )

        # stage ?: request phone_number
        signals.require_phone_number_signal.emit(task)
        # state ?: await otp

        return True
    except Exception as e:
        if "ERR_PROXY_NOT_READY" == str(e) or "ERR_TIMED_OUT" in str(e):
            raise e
        error_type = type(e).__name__
        error_message = str(e)
        full_traceback = traceback.format_exc()

        # print(
        #     f"{log_prefix} UNEXPECTED ERROR: A general error occurred during task execution:",
        #     file=sys.stderr,
        # )
        # print(f"  Error Type: {error_type}", file=sys.stderr)
        # print(f"  Message: {error_message}", file=sys.stderr)
        # print(f"  Traceback Details:\n{full_traceback}", file=sys.stderr)

        msg = f"\t\t❌ ERROR [{task.user_info.username} - {task.user_info.username}]({task.action_name}): {error_type}"
        print(msg)

        # signals.error_signal.emit(
        #     task,
        #     f"Unexpected error: {error_message}\nDetails: See console log for full traceback.",
            
        # )
        return False
