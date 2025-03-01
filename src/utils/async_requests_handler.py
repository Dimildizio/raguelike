import threading
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AsyncRequest:
    request_type: str
    entity: Any
    content: Optional[str] = None


class AsyncRequestHandler:
    def __init__(self):
        self.pending_requests = []
        self.completed_requests = []
        self.lock = threading.Lock()
        self.current_thread = None

    def add_request(self, request_type: str, entity: Any):
        """Add a new async request"""
        with self.lock:
            self.pending_requests.append(AsyncRequest(request_type, entity))

    def process_requests(self, dialogue_processor):
        """Process pending requests in a separate thread"""
        # If there's no current thread or it's finished
        if not self.current_thread or not self.current_thread.is_alive():
            if self.pending_requests:
                with self.lock:
                    request = self.pending_requests.pop(0)

                def process_request(request):
                    try:
                        if request.request_type == 'shout':
                            txt = request.entity.get_shout_prompt()
                            shout = dialogue_processor.process_shouts(txt)
                            with self.lock:
                                request.content = shout
                                self.completed_requests.append(request)
                    except Exception as e:
                        print(f"Error processing async request: {e}")
                        self.completed_requests.append(request)

                self.current_thread = threading.Thread(target=process_request, args=(request,))
                self.current_thread.daemon = True
                self.current_thread.start()

    def get_completed_requests(self):
        """Get and clear completed requests"""
        with self.lock:
            completed = self.completed_requests.copy()
            self.completed_requests.clear()
            return completed