# src/_robot/actions/launch_browser.py
from typing import List, Union
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from src.my_types import (
    BrowserTaskType,
    BrowserWorkerSignals,
    LaunchPayloadType,
    RobotSettingsType,
)
import sys, traceback

MIN = 60_000


def launch_browser(
    page: Page,
    task: BrowserTaskType,
    settings: RobotSettingsType,
    signals: BrowserWorkerSignals,
) -> Union[bool, str]:
    action_payload: LaunchPayloadType = task.action_payload
    log_prefix = f"[Task {task.user_info.username} - launch_browser]"
    progress: List[int] = [0, 4]  # current, total

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    try:
        emit_progress_update("Launching browser...")
        try:
            page.goto(action_payload.url, timeout=MIN)
            emit_progress_update("Successfully navigated to URL.")
        except PlaywrightTimeoutError as e:
            emit_progress_update(f"ERROR: Timeout while navigating to URL.")
            print(
                f"{log_prefix} ERROR: Timeout when navigating to URL: {e}",
                file=sys.stderr,
            )
            raise Exception("ERR_PROXY_NOT_READY")
        except Exception as e:
            if "ERR_ABORTED" in str(e):
                pass
            elif "ERR_TIMED_OUT" in str(e):
                pass
            elif "ERR_TOO_MANY_REDIRECTS" in str(e):
                pass
            else:
                emit_progress_update(
                    f"ERROR: An unexpected error occurred during navigation."
                )
                print(
                    f"{log_prefix} ERROR: An unexpected error occurred during navigation: {e}",
                    file=sys.stderr,
                )
                return False

        emit_progress_update("Waiting for browser to close event (if applicable).")
        page.wait_for_event("close", timeout=0)
        emit_progress_update("Browser launched and ready. Waiting for task completion.")
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
