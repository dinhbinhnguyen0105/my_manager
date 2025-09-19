import uuid
from datetime import datetime
from typing import List, Dict, Tuple
from collections import deque
from PyQt6.QtCore import QThreadPool, QObject, pyqtSlot, QTimer
from PyQt6.QtGui import QGuiApplication

from src.robot.browser_worker import BrowserWorker
from src.my_types import (
    BrowserTaskType,
    BrowserWorkerSignals,
    BrowserManagerSignals,
    RobotSettingsType,
)


class BrowserManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending_browsers: deque[BrowserTaskType] = deque()
        self._pending_raw_proxies: deque[str] = deque()
        self._in_progress_tasks: Dict[str, dict] = {}
        self._total_task_num: int = 0
        self._settings = RobotSettingsType(
            is_mobile=False,
            headless=False,
            thread_num=8,
            group_num=0,
            delay_num=0,
            group_file_path="",
        )
        self._raw_proxies: set[str] = set()
        self.manager_signals = BrowserManagerSignals()
        self.worker_signals = BrowserWorkerSignals()
        self._max_threads: int = 8  # Số luồng tối đa có thể chạy đồng thời
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self._screen_size = (screen_geometry.width(), screen_geometry.height())

        # --- LOGIC MỚI CHO VỊ TRÍ CỬA SỔ ---
        self._available_window_positions: deque[Tuple[int, int]] = deque()
        self._max_cols = 16  # Số cột tối đa bạn muốn xếp browser trên màn hình
        # Kích thước cửa sổ browser mặc định (desktop) để tính toán vị trí
        self._window_desktop_width = 960 if not self._settings.is_mobile else 375
        self._window_desktop_height = int(
            self._window_desktop_width * 0.56
            if not self._settings.is_mobile
            else self._window_desktop_width * 1.5
        )

        self._initialize_window_positions()
        # --- KẾT THÚC LOGIC MỚI ---

        self.worker_signals.info_signal.connect(self.on_info)
        self.worker_signals.warning_signal.connect(self.on_warning)
        self.worker_signals.failed_signal.connect(self.on_failed)
        self.worker_signals.error_signal.connect(self.on_error)
        self.worker_signals.progress_signal.connect(self.on_progress)
        self.worker_signals.finished_signal.connect(self.on_task_succeed)
        self.worker_signals.proxy_unavailable_signal.connect(self.on_proxy_unavailable)
        self.worker_signals.proxy_not_ready_signal.connect(self.on_proxy_not_ready)
        self.worker_signals.require_phone_number_signal.connect(
            self.on_require_phone_number
        )
        self.worker_signals.require_otp_code_signal.connect(self.on_require_otp_code)
        self.threadpool = QThreadPool.globalInstance()

    def _initialize_window_positions(self):
        """
        Calculates 16 window positions in a grid, wrapping to the next row
        with a 200px offset when the screen edge is reached.
        """
        screen_width = self._screen_size[0]
        screen_height = self._screen_size[1]

        # Fixed number of positions to generate
        total_positions = 16

        # Offset for next row/col
        offset = 200

        # Store the final list of valid positions
        # self._available_window_positions = []

        # Keep track of the current position to calculate the next
        pos_x = 0
        pos_y = 0

        for i in range(total_positions):
            # Add the current position to the list
            self._available_window_positions.append((pos_x, pos_y))

            # Calculate the next potential position
            next_pos_x = pos_x + offset

            # Check if the next position exceeds the screen width
            if next_pos_x + self._window_desktop_width > screen_width:
                # If it does, wrap to the next row
                pos_x = 0
                pos_y += offset

                # Check if the new row position is off-screen. If so, stop.
                if pos_y + self._window_desktop_height > screen_height:
                    break
            else:
                # If it doesn't, just move to the next column
                pos_x = next_pos_x

    def add_browsers(
        self, list_browsers: List[BrowserTaskType], list_raw_proxies: List[str]
    ):
        for browser in list_browsers:
            self._pending_browsers.append(browser)
            self._total_task_num += 1

        for proxy in list_raw_proxies:
            if proxy not in self._raw_proxies:
                self._raw_proxies.add(proxy)
                self._pending_raw_proxies.append(proxy)

        self.try_start_browsers()

    def try_start_browsers(self):
        """Cố gắng khởi động các browser worker mới."""
        # Số vị trí trống trong thread pool (số worker có thể chạy thêm)
        available_slots_in_pool = (
            self._max_threads - self.threadpool.activeThreadCount()
        )

        # Số vị trí cửa sổ có sẵn trên màn hình
        available_window_slots = len(self._available_window_positions)

        # Số lượng tác vụ mới có thể khởi động dựa trên tất cả các ràng buộc
        num_to_start = min(
            available_slots_in_pool,
            available_window_slots,
            len(self._pending_browsers),
            len(self._pending_raw_proxies),
        )
        # print(
        #     {
        #         "active_thread": self.threadpool.activeThreadCount(),
        #         "thread_num": self._max_threads,
        #         "pending_tasks_num": len(self._pending_browsers),
        #         "pending_proxy_num": len(self._pending_raw_proxies),
        #         "window_pos": len(self._available_window_positions),
        #     }
        # )
        while (
            self.threadpool.activeThreadCount() <= self._max_threads
            and len(self._in_progress_tasks) < self._max_threads
            and self._pending_browsers
            and self._pending_raw_proxies
            # and self._available_window_positions
        ):
            browser = self._pending_browsers.popleft()
            raw_proxy = self._pending_raw_proxies.popleft()

            # Lấy một vị trí cửa sổ có sẵn
            window_position = self._available_window_positions.popleft()

            worker = BrowserWorker(
                browser=browser,
                raw_proxy=raw_proxy,
                settings=self._settings,
                signals=self.worker_signals,
                worker_position=window_position,
                screen_size=self._screen_size,
                info={
                    "active_thread": self.threadpool.activeThreadCount(),
                    "max_threads": self._max_threads,
                    "pending_task_num": len(self._pending_browsers),
                    "pending_proxy_num": len(self._pending_raw_proxies),
                },
            )
            while browser.browser_id in self._in_progress_tasks:
                browser.browser_id = str(uuid.uuid4())
            self._in_progress_tasks[browser.browser_id] = {
                "browser": browser,
                "raw_proxy": raw_proxy,
                "worker": worker,
                "window_position": window_position,
            }
            self.threadpool.start(worker)

        # print(f"\rPending tasks: {len(self._pending_browsers)}{' ' * 20}", end="")
        if (
            not self._pending_browsers
            and not self._in_progress_tasks
            and len(self._pending_raw_proxies) == len(self._raw_proxies)
        ):
            print("All tasks finished!")
            self.manager_signals.finished_signal.emit("All tasks finished!")

    def is_all_task_finished(self) -> bool:
        return not self._pending_browsers and not self._in_progress_tasks

    # --------------------- setter --------------------- #
    def set_settings(self, settings: RobotSettingsType):
        self._settings = settings
        # Cập nhật _max_threads từ settings.thread_num
        self._max_threads = settings.thread_num
        # Nếu _max_threads thay đổi hoặc các thông số kích thước cửa sổ thay đổi,
        # bạn có thể cần khởi tạo lại _available_window_positions.
        # Tuy nhiên, hãy cẩn thận để không làm mất các vị trí đang được sử dụng.
        # Với thiết kế hiện tại, chúng ta giả định _max_threads được thiết lập khi khởi động.
        # Nếu muốn thay đổi dynamic, cần phức tạp hơn một chút.

    # --------------------- BrowserWorkerSignals slots --------------------- #
    @pyqtSlot(BrowserTaskType, str)
    def on_info(self, browser: BrowserTaskType, message: str):
        msg = f"ℹ️ INFO [{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): {message}"
        self.manager_signals.info_signal.emit(msg)

    @pyqtSlot(BrowserTaskType, str)
    def on_warning(self, browser: BrowserTaskType, message: str):
        msg = f"\t\t⚠️ WARNING [{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): {message}"
        self.manager_signals.warning_signal.emit(msg)

    @pyqtSlot(BrowserTaskType, str, str)
    def on_failed(self, browser: BrowserTaskType, message: str, raw_proxy: str):
        msg = f"\t\t❗[{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): {message}"
        self.manager_signals.failed_signal.emit(msg)

        # Thêm proxy vào hàng chờ lại (có thể thử lại sau)

        # Xóa tác vụ khỏi danh sách đang chạy và giải phóng vị trí cửa sổ
        if browser.browser_id in self._in_progress_tasks:
            pos_to_release = self._in_progress_tasks[browser.browser_id][
                "window_position"
            ]
            self._available_window_positions.appendleft(
                pos_to_release
            )  # Giải phóng vị trí
            if raw_proxy not in self._pending_raw_proxies:
                self._pending_raw_proxies.append(raw_proxy)
            del self._in_progress_tasks[browser.browser_id]
            # print(f"Released position {pos_to_release} for {browser.user_info.username} (failed).")
        self.try_start_browsers()  # Cố gắng khởi động tác vụ mới

    @pyqtSlot(BrowserTaskType, str)
    def on_error(self, browser: BrowserTaskType, message: str):
        msg = f"\t\t❌ ERROR [{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): {message}"
        self.manager_signals.error_signal.emit(msg)

        # if raw_proxy not in self._pending_raw_proxies:
        #     self._pending_raw_proxies.append(raw_proxy)

        # Xóa tác vụ khỏi danh sách đang chạy và giải phóng vị trí cửa sổ
        if browser.browser_id in self._in_progress_tasks:
            pos_to_release = self._in_progress_tasks[browser.browser_id][
                "window_position"
            ]
            self._available_window_positions.appendleft(
                pos_to_release
            )  # Giải phóng vị trí
            del self._in_progress_tasks[browser.browser_id]
            # print(f"Released position {pos_to_release} for {browser.user_info.username} (error).")
        self.try_start_browsers()  # Cố gắng khởi động tác vụ mới

    @pyqtSlot(BrowserTaskType, str, list)
    def on_progress(self, browser: BrowserTaskType, message: str, progressing: List):
        msg = f"💬 PROGRESS [{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): {message}"
        self.manager_signals.progress_signal.emit(msg, progressing)

    @pyqtSlot(BrowserTaskType, str, str)
    def on_task_succeed(self, browser: BrowserTaskType, message: str, raw_proxy: str):
        msg = f"✅ SUCCEED [{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): {message}"
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {browser.user_info.username}"
        )
        self.manager_signals.task_succeed_signal.emit(msg)

        # Thêm proxy vào hàng chờ lại (sẵn sàng cho tác vụ khác)

        # Xóa tác vụ khỏi danh sách đang chạy và giải phóng vị trí cửa sổ
        if browser.browser_id in self._in_progress_tasks:
            pos_to_release = self._in_progress_tasks[browser.browser_id][
                "window_position"
            ]
            if raw_proxy not in self._pending_raw_proxies:
                self._pending_raw_proxies.append(raw_proxy)
            self._available_window_positions.appendleft(
                pos_to_release
            )  # Giải phóng vị trí
            del self._in_progress_tasks[browser.browser_id]
            # print(f"Released position {pos_to_release} for {browser.user_info.username} (succeeded).")
        self.try_start_browsers()  # Cố gắng khởi động tác vụ mới

    @pyqtSlot(BrowserTaskType, str)
    def on_proxy_unavailable(self, browser: BrowserTaskType, raw_proxy: str):
        msg = f"⚠️ PROXY [{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): Unavailable proxy ({raw_proxy})"
        self.manager_signals.warning_signal.emit(msg)

        # Đẩy browser task về đầu hàng chờ để thử lại với proxy khác
        self._pending_browsers.appendleft(browser)

        # Xóa tác vụ khỏi danh sách đang chạy và giải phóng vị trí cửa sổ
        if browser.browser_id in self._in_progress_tasks:
            pos_to_release = self._in_progress_tasks[browser.browser_id][
                "window_position"
            ]
            self._available_window_positions.appendleft(
                pos_to_release
            )  # Giải phóng vị trí
            del self._in_progress_tasks[browser.browser_id]
            # print(f"Released position {pos_to_release} for {browser.user_info.username} (proxy unavailable).")
        self.try_start_browsers()  # Cố gắng khởi động tác vụ mới

    @pyqtSlot(BrowserTaskType, str)
    def on_proxy_not_ready(self, browser: BrowserTaskType, raw_proxy: str):
        msg = (
            f"⚠️ PROXY [{browser.user_info.uid} - {browser.user_info.username}]({browser.action_name}): "
            f"Could not use proxy ({raw_proxy}), will retry with this proxy after 10s."
        )
        self.manager_signals.warning_signal.emit(msg)

        # Xóa tác vụ khỏi danh sách đang chạy và giải phóng vị trí cửa sổ NGAY LẬP TỨC
        if browser.browser_id in self._in_progress_tasks:
            pos_to_release = self._in_progress_tasks[browser.browser_id][
                "window_position"
            ]
            self._available_window_positions.appendleft(
                pos_to_release
            )  # Giải phóng vị trí
            del self._in_progress_tasks[browser.browser_id]
            # print(f"Released position {pos_to_release} for {browser.user_info.username} (proxy not ready).")

        # Đẩy tác vụ về đầu hàng chờ để nó được ưu tiên thử lại
        self._pending_browsers.appendleft(browser)

        # Delay 10s trước khi thử lại khởi động browser
        # _msg = f"Will retry with {raw_proxy} after 10 seconds."
        # print(_msg, end="\r")

        def call_start():
            # Đẩy proxy này về cuối hàng chờ, cho phép nó "hạ nhiệt"
            if raw_proxy not in self._pending_raw_proxies:
                self._pending_raw_proxies.append(raw_proxy)

            # print(" " * len(_msg), end="\r")
            # print(new_message, end="\r")
            self.try_start_browsers()

        QTimer.singleShot(10000, call_start)
        # Kích hoạt lại try_start_browsers để lấp đầy các luồng trống ngay lập tức
        # (tác vụ vừa bị đẩy lại hàng chờ sẽ được xử lý sau 10s hoặc khi có proxy khác)
        # self.try_start_browsers()

    @pyqtSlot(BrowserTaskType)
    def on_require_phone_number(self, browser: BrowserTaskType):
        # ❓ Logic xử lý khi cần số điện thoại (ví dụ: hiển thị dialog cho người dùng)
        # Tùy thuộc vào cách bạn muốn xử lý, bạn có thể tạm dừng tác vụ, hiển thị GUI, v.v.
        self.manager_signals.require_phone_number_signal.emit(browser)
        # Quan trọng: Nếu bạn tạm dừng tác vụ ở đây, hãy đảm bảo giải phóng vị trí cửa sổ
        # và quản lý việc tiếp tục tác vụ sau khi có thông tin.
        if browser.browser_id in self._in_progress_tasks:
            pos_to_release = self._in_progress_tasks[browser.browser_id][
                "window_position"
            ]
            self._available_window_positions.appendleft(pos_to_release)
            del self._in_progress_tasks[browser.browser_id]
            print(
                f"Paused task {browser.user_info.username} for phone number, released position {pos_to_release}."
            )
        self.try_start_browsers()

    @pyqtSlot(BrowserTaskType)
    def on_require_otp_code(self, browser: BrowserTaskType):
        # ❓ Logic xử lý khi cần mã OTP (ví dụ: hiển thị dialog cho người dùng)
        self.manager_signals.require_otp_code_signal.emit(browser)
        # Tương tự như on_require_phone_number
        if browser.browser_id in self._in_progress_tasks:
            pos_to_release = self._in_progress_tasks[browser.browser_id][
                "window_position"
            ]
            self._available_window_positions.appendleft(pos_to_release)
            del self._in_progress_tasks[browser.browser_id]
            print(
                f"Paused task {browser.user_info.username} for OTP, released position {pos_to_release}."
            )
        self.try_start_browsers()
