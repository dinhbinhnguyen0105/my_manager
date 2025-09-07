import pycurl
import io
import json
from typing import List, Tuple, Dict
from collections import deque

from PyQt6.QtCore import QThreadPool, QRunnable, QObject, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
    """
    Signals available from a running worker thread.

    success_signal: Emits (uid, is_live) on successful check.
    error_signal: Emits (uid, error_message) on failure.
    finished: Emits uid when the worker finishes (success or error).
    """

    success_signal = pyqtSignal(str, bool)
    error_signal = pyqtSignal(str, str)
    finished = pyqtSignal(str)


class CheckLiveWorker(QRunnable):
    """
    Worker to perform a single check for a UID using pycurl.
    """

    def __init__(self, uid: str):
        super().__init__()
        self.uid = uid
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self):
        buffer = io.BytesIO()
        curl = pycurl.Curl()
        url = f"https://graph.facebook.com/{self.uid}/picture?redirect=false"
        headers = [
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept: application/json",
            "Accept-Language: en-US,en;q=0.9",
            "Connection: keep-alive",
        ]

        try:
            curl.setopt(pycurl.URL, url)
            curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
            curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            curl.setopt(pycurl.TIMEOUT, 20)
            curl.setopt(pycurl.FOLLOWLOCATION, 1)
            curl.setopt(pycurl.HTTPHEADER, headers)
            curl.perform()

            status_code = curl.getinfo(pycurl.RESPONSE_CODE)
            body = buffer.getvalue().decode("utf-8", errors="ignore")

            if status_code != 200:
                error_msg = f"HTTP Error {status_code} for UID {self.uid}. Response: {body[:200]}..."
                self.signals.error_signal.emit(self.uid, error_msg)
                self.signals.success_signal.emit(self.uid, False)
            else:
                try:
                    data = json.loads(body)
                    is_live = bool(data.get("data", {}).get("height", False))
                    self.signals.success_signal.emit(self.uid, is_live)
                except json.JSONDecodeError as e:
                    error_msg = f"JSON Decode Error for UID {self.uid}: {e}. Response: {body[:200]}..."
                    self.signals.error_signal.emit(self.uid, error_msg)

        except pycurl.error as e:
            errno, errstr = e.args
            error_msg = f"PyCurl error {errno}: {errstr} for UID {self.uid}"
            self.signals.error_signal.emit(self.uid, error_msg)

        except Exception as e:
            error_msg = f"Unexpected error for UID {self.uid}: {e}"
            self.signals.error_signal.emit(self.uid, error_msg)

        finally:
            curl.close()
            buffer.close()
            self.signals.finished.emit(self.uid)


class CheckLive(QObject):
    """
    Manages a queue of CheckLiveWorker tasks using a QThreadPool,
    handling concurrency and progress reporting.
    Now accepts list of (id, uid) tuples and emits id in success signal.
    """

    task_succeeded = pyqtSignal(int, str, bool)
    task_failed = pyqtSignal(int, str, str)
    all_tasks_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending_tasks: deque[Tuple[int, str]] = deque()
        self._in_progress: Dict[str, Tuple[int, CheckLiveWorker]] = {}
        self._failed: Dict[int, str] = {}
        self._succeeded: Dict[int, bool] = {}
        self._total_tasks = 0

        self.threadpool = QThreadPool.globalInstance()
        max_workers = min(5, self.threadpool.maxThreadCount())
        self.threadpool.setMaxThreadCount(max_workers)

    @pyqtSlot(list)
    def add_tasks(self, tasks: List[Tuple[int, str]]):
        """
        Accepts list of (id, uid) tuples.
        """
        seen_uids = set(uid for _, uid in self._pending_tasks) | set(
            self._in_progress.keys()
        )
        for record_id, uid in tasks:
            if uid not in seen_uids:
                self._pending_tasks.append((record_id, uid))
                self._total_tasks += 1
                seen_uids.add(uid)

        self._try_start_tasks()

    def _try_start_tasks(self):
        """
        Start queued tasks up to max concurrency.
        """
        available = (
            self.threadpool.maxThreadCount() - self.threadpool.activeThreadCount()
        )
        while available > 0 and self._pending_tasks:
            record_id, uid = self._pending_tasks.popleft()
            worker = CheckLiveWorker(uid)
            worker.signals.success_signal.connect(self._on_success)
            worker.signals.error_signal.connect(self._on_error)
            worker.signals.finished.connect(self._on_finished)

            self._in_progress[uid] = (record_id, worker)
            self.threadpool.start(worker)
            available -= 1

    @pyqtSlot(str, bool)
    def _on_success(self, uid: str, is_live: bool):
        record_id, _ = self._in_progress.get(uid, (None, None))
        if record_id is not None:
            self._succeeded[record_id] = is_live
            self.task_succeeded.emit(record_id, uid, is_live)
        self._try_start_tasks()

    @pyqtSlot(str, str)
    def _on_error(self, uid: str, error_msg: str):
        record_id, _ = self._in_progress.get(uid, (None, None))
        if record_id is not None:
            self._failed[record_id] = error_msg
            self.task_failed.emit(record_id, uid, error_msg)

    @pyqtSlot(str)
    def _on_finished(self, uid: str):
        if uid in self._in_progress:
            del self._in_progress[uid]
        if not self._pending_tasks and not self._in_progress:
            self.all_tasks_finished.emit()

    def _check_if_done(self) -> bool:
        """
        Checks if all tasks have been completed (succeeded or failed).
        """
        is_done = not self._pending_tasks and not self._in_progress
        processed_count = len(self._succeeded) + len(self._failed)
        if self._total_tasks > 0 and processed_count != self._total_tasks:
            print(
                f"[{self.__class__.__name__}._check_if_done] Warning: Processed count ({processed_count}) does not match total tasks ({self._total_tasks})."
            )
            return False
        return is_done

    def get_results(self) -> Dict[int, bool]:
        return self._succeeded

    def get_failed(self) -> Dict[int, str]:
        return self._failed
