import threading
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from undetected_playwright import Tarnished
from typing import Tuple, Dict, Any

from PyQt6.QtCore import QEventLoop, QTimer, QRunnable

from src.my_types import BrowserWorkerSignals, BrowserTaskType, RobotSettingsType
from src.robot.action_mapping import ACTION_MAP
from src.utils.get_proxy import get_proxy
import json
import os
from src.robot.actions import fb_utils  # Đảm bảo fb_utils được dùng hoặc xóa nếu không

UDD_LOCKS = {}


class BrowserWorker(QRunnable):
    def __init__(
        self,
        browser: BrowserTaskType,
        raw_proxy: str,
        signals: BrowserWorkerSignals,
        settings: RobotSettingsType,
        worker_position: Tuple[
            int, int
        ],  # Tham số mới: vị trí (x,y) được gán từ Manager
        screen_size: Tuple[int, int],
        info: Dict[str, Any],
    ):
        super().__init__()
        self._browser = browser
        self._raw_proxy = raw_proxy
        self._signals = signals
        self._settings = settings
        self._worker_position = worker_position  # Lưu vị trí đã nhận
        self._screen_size = screen_size
        self._info = info
        # info={
        #     "active_thread": self.threadpool.activeThreadCount(),
        #     "max_threads": self._max_threads,
        #     "pending_task_num": len(self._pending_browsers),
        #     "pending_proxy_num": len(self._pending_raw_proxies),
        # }

        self.setAutoDelete(True)  # Đảm bảo worker tự xóa sau khi hoàn thành

    def run(self):
        # Xác định chế độ mobile/desktop trước khi tạo context_kwargs
        is_mobile_mode = self._browser.is_mobile or (
            self._browser.action_name == "share_latest_product"
        )

        try:
            context_kwargs = dict(
                user_data_dir=self._browser.udd,
                user_agent=(
                    self._browser.user_info.mobile_ua
                    if is_mobile_mode
                    else self._browser.user_info.desktop_ua
                ),
                headless=self._browser.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    f'--app-name=Chromium - {self._browser.user_info.username or "Unknown User"}',
                ],
                ignore_default_args=["--enable-automation"],
            )

            # --- Cấu hình kích thước cửa sổ và viewport ---
            # Kích thước mặc định cho desktop (sẽ được ghi đè nếu là mobile)
            window_width = 960
            window_height = int(window_width * 0.56)

            context_kwargs["device_scale_factor"] = 0.68  # Một yếu tố scale chung

            if is_mobile_mode:
                window_width = 375  # Chiều rộng tiêu chuẩn cho mobile
                window_height = int(window_width * 1.5)  # Tỉ lệ cao hơn cho mobile
                context_kwargs["viewport"] = {
                    "width": window_width,
                    "height": window_height,
                }
                context_kwargs["screen"] = (
                    {  # Screen size thường giống viewport cho mobile
                        "width": window_width,
                        "height": window_height,
                    }
                )
                context_kwargs["is_mobile"] = True
                context_kwargs["has_touch"] = True
            else:  # Desktop mode
                # Kích thước window_width/height đã được đặt ở trên
                context_kwargs["viewport"] = {
                    "width": window_width,
                    "height": window_height,
                }
                context_kwargs["screen"] = {
                    "width": window_width,
                    "height": window_height,
                }
                context_kwargs["is_mobile"] = False
                context_kwargs["has_touch"] = False

            # --- SỬ DỤNG VỊ TRÍ ĐƯỢC CẤP PHÁT TỪ BrowserManager ---
            pos_x = self._worker_position[0]
            pos_y = self._worker_position[1]

            context_kwargs["args"].append(f"--window-position={pos_x},{pos_y}")
            # --- KẾT THÚC CẤU HÌNH CỬA SỔ ---

            udd = self._browser.udd
            # Đảm bảo chỉ một worker truy cập cùng một user data directory tại một thời điểm
            if udd not in UDD_LOCKS:
                UDD_LOCKS[udd] = threading.Lock()
            with UDD_LOCKS[udd]:
                proxy = self.BrowserWorker__handle_get_proxy()
                if proxy == 0:
                    self._signals.error_signal.emit(
                        self._browser,
                        f"Unknown proxy error",
                    )
                    print("proxy error")
                    return
                elif proxy == -1:
                    self._signals.proxy_not_ready_signal.emit(
                        self._browser, self._raw_proxy
                    )
                    return
                elif proxy == -2:
                    self._signals.proxy_unavailable_signal.emit(
                        self._browser, self._raw_proxy
                    )
                    print("proxy error")
                    return
                # Chỉ tiếp tục nếu có proxy hợp lệ và action_name có trong ACTION_MAP
                elif (
                    proxy
                    and type(proxy) == dict
                    and self._browser.action_name in ACTION_MAP.keys()
                ):
                    with sync_playwright() as p:
                        print(
                            f"[{datetime.now().strftime('%H:%M:%S')}] Started worker for {self._browser.user_info.username.replace("\n", "")} ({self._info['pending_task_num']} tasks in pending)."
                        )

                        # datetime.now()

                        context_kwargs["proxy"] = proxy  # Áp dụng proxy cho context
                        context = p.chromium.launch_persistent_context(**context_kwargs)
                        Tarnished.apply_stealth(
                            context
                        )  # Áp dụng các kỹ thuật anti-detection

                        # Sử dụng page hiện có hoặc tạo page mới
                        pages = context.pages
                        if pages:
                            current_page = pages[0]
                        else:
                            current_page = context.new_page()

                        # Đặt nội dung trang thông tin để dễ debug
                        info_html = f"""
        <html>
            <head><title>{self._browser.user_info.username.replace("\n", "")}</title></head>
            <body>
                <h2>username: {self._browser.user_info.username.replace("\n", "")}</h2>
                <p>id: {self._browser.user_info.id}</p>
                <p>uid: {self._browser.user_info.uid}</p>
                <p>user_data_dir: {self._browser.udd}</p>
            </body>
        </html>
    """
                        current_page.set_content(info_html)

                        # Tạo một page mới để thực hiện hành động chính
                        page = context.new_page()
                        ACTION_HANDLER = ACTION_MAP[
                            self._browser.action_name
                        ]  # Lấy handler cho action

                        try:
                            result = ACTION_HANDLER(  # Thực thi hành động
                                page,
                                self._browser,
                                self._settings,
                                self._signals,
                            )
                            if self._browser.action_name == "list_on_group_and_share":
                                result_file = "results.json"
                                result_lock = threading.Lock()

                                # Đảm bảo kết quả là kiểu dict hoặc có thể serialize
                                result_data = {
                                    "username": self._browser.user_info.username,
                                    "action": self._browser.action_name,
                                    "result": result,
                                    "timestamp": datetime.now().isoformat(),
                                }

                                with result_lock:
                                    # Đọc dữ liệu cũ nếu file đã tồn tại
                                    if os.path.exists(result_file):
                                        with open(
                                            result_file, "r", encoding="utf-8"
                                        ) as f:
                                            try:
                                                all_results = json.load(f)
                                            except Exception:
                                                all_results = []
                                    else:
                                        all_results = []

                                    all_results.append(result_data)

                                    # Ghi lại dữ liệu mới
                                    with open(result_file, "w", encoding="utf-8") as f:
                                        json.dump(
                                            all_results, f, ensure_ascii=False, indent=2
                                        )

                        except PlaywrightTimeoutError:
                            # Xử lý lỗi timeout của Playwright
                            self._signals.proxy_not_ready_signal.emit(
                                self._browser,
                                self._raw_proxy,
                            )
                        except Exception as e:
                            # Xử lý các loại lỗi khác
                            error_msg = str(e)
                            print(
                                f"ℹ️ [{self._browser.user_info.username.replace("\n", "")}] Error: {error_msg[:100]}..."
                            )  # Log 100 ký tự đầu

                            # Kiểm tra các lỗi liên quan đến proxy/mạng để phát tín hiệu phù hợp
                            if (
                                "ERR_PROXY_NOT_READY" in error_msg
                                or "ERR_TIMED_OUT" in error_msg
                            ):
                                self._signals.proxy_not_ready_signal.emit(
                                    self._browser,
                                    self._raw_proxy,
                                )
                            elif (
                                "ERR_ABORTED" in error_msg
                                or "ERR_TOO_MANY_REDIRECTS" in error_msg
                                or "net::ERR" in error_msg
                            ):
                                # Các lỗi mạng hoặc redirect, có thể coi là proxy không ổn định hoặc lỗi tạm thời
                                self._signals.proxy_not_ready_signal.emit(  # Hoặc proxy_unavailable_signal tùy theo mức độ nghiêm trọng
                                    self._browser,
                                    self._raw_proxy,
                                )
                            else:
                                # Các lỗi khác không liên quan đến proxy, coi là lỗi tác vụ
                                self._signals.failed_signal.emit(
                                    self._browser, error_msg, self._raw_proxy
                                )

                        # Chờ một khoảng thời gian trước khi đóng browser (nếu có delay_num)
                        delay_ms = int(self._settings.delay_num * 60 * 1000)
                        if delay_ms > 0:
                            loop = QEventLoop()
                            QTimer.singleShot(delay_ms, loop.quit)
                            loop.exec()

        except Exception as e:
            # Xử lý các lỗi xảy ra trong quá trình khởi tạo browser hoặc proxy
            error_msg = str(e)
            if "ERR_PROXY_NOT_READY" in error_msg or "ERR_TIMED_OUT" in error_msg:
                self._signals.proxy_not_ready_signal.emit(
                    self._browser, self._raw_proxy
                )
            elif "ERR_PROXY_CONNECTION_FAILED" in error_msg:
                self._signals.proxy_unavailable_signal.emit(
                    self._browser, self._raw_proxy
                )
            else:
                self._signals.failed_signal.emit(
                    self._browser, error_msg, self._raw_proxy
                )

        finally:
            # Đảm bảo context được đóng ngay cả khi có lỗi (nếu context đã được mở)
            # Dù `with sync_playwright() as p:` sẽ xử lý phần lớn,
            # một số lỗi có thể xảy ra trước khi context được gán.
            try:
                if "context" in locals() and context:
                    context.close()
            except Exception as e:
                # print(f"Error closing browser context: {e}")
                pass

            # Đảm bảo lock được release khi worker hoàn thành hoặc lỗi
            if udd in UDD_LOCKS and UDD_LOCKS[udd].locked():
                UDD_LOCKS[udd].release()
            # Phát tín hiệu hoàn thành tác vụ
            self._signals.finished_signal.emit(
                self._browser, "Finished", self._raw_proxy
            )

    def BrowserWorker__handle_get_proxy(self):
        """Xử lý việc lấy thông tin proxy."""
        try:
            res = get_proxy(self._raw_proxy)
            status_code_str = res.get("status")  # Lấy status dưới dạng string

            # Kiểm tra và chuyển đổi status_code an toàn
            if status_code_str is None:
                self._signals.failed_signal.emit(
                    self._browser,
                    "Proxy service response missing 'status' field.",
                    self._raw_proxy,
                )
                return 0

            try:
                status_code = int(status_code_str)
            except ValueError:
                self._signals.error_signal.emit(
                    self._browser,
                    f"Invalid proxy status code format: {status_code_str}",
                )
                return 0

            if status_code == 100:
                proxy = res.get("data")
            elif status_code == 101:
                return -1
            elif status_code == 102:
                return -2
            else:  # Xử lý các mã trạng thái không mong muốn khác
                return 0
            return proxy
        except Exception as e:
            return 0  # Đảm bảo trả về None khi có lỗi
