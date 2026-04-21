import threading
import queue
import traceback

class AsyncTaskRunner:
    """
    Tiện ích chạy tác vụ trong luồng riêng biệt để tránh treo giao diện Tkinter.
    """
    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self._check_queue()

    def run_task(self, task_func, args=(), callback=None, error_callback=None):
        """
        Chạy một hàm trong background thread.
        
        Args:
            task_func: Hàm cần chạy
            args: Các đối số cho hàm
            callback: Hàm gọi lại khi thành công (nhận kết quả là tham số đầu tiên)
            error_callback: Hàm gọi lại khi có lỗi (nhận exception là tham số đầu tiên)
        """
        def thread_target():
            try:
                result = task_func(*args)
                self.queue.put(("SUCCESS", callback, result))
            except Exception as e:
                print(f"Error in background task: {e}")
                traceback.print_exc()
                self.queue.put(("ERROR", error_callback, e))

        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()

    def _check_queue(self):
        """Kiểm tra hàng đợi định kỳ để thực hiện callback trên main thread."""
        try:
            while True:
                msg_type, func, data = self.queue.get_nowait()
                if func:
                    func(data)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._check_queue)
