import threading
import subprocess
import time

class NetworkMonitorCore:
    """
    Core processing module that connects an input adapter with one or more output adapters.
    It calls input_adapter.start(self.process_event) and dispatches each aggregated event to all output adapters.
    """
    def __init__(self, input_adapter, output_adapters: list):
        self.input_adapter = input_adapter
        self.output_adapters = output_adapters if isinstance(output_adapters, list) else [output_adapters]
        self._running = False

    def start(self):
        if self._running:
            print("[Core] Warning: Monitoring already running.")
            return

        print("[Core] Starting network monitoring...")
        self._running = True
        self.input_adapter.start()

        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[Core] Shutting down gracefully.")
            self.stop()
        except Exception as e:
            print(f"[Core] Error during monitoring: {e}")
            self.stop()

    def process_event(self, event):
        print(f"[Core] Processing event: {event}")
        for adapter in self.output_adapters:
            adapter.handle_event(event)

    def stop(self):
        print("[Core] Stopping network monitoring...")
        
        self._running = False
        if self.input_adapter:
            self.input_adapter.stop()
        for adapter in self.output_adapters:
            if hasattr(adapter, "stop"):
                adapter.stop()
        print("[Debug] Active threads at shutdown:")
        for t in threading.enumerate():
            print(f" - {t.name} (daemon={t.daemon})")

class NetworkConnectivityMonitor:
    def __init__(self, on_failure, check_interval=10, max_failures=3):
        self.on_failure = on_failure
        self.check_interval = check_interval
        self.max_failures = max_failures
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def _run(self):
        failure_count = 0
        while not self._stop.is_set():
            bridge_ok = self._ping("192.168.0.192")
            internet_ok = self._ping("8.8.8.8")
            if not bridge_ok and not internet_ok:
                failure_count += 1
                print(f"[NetCheck] Connectivity check failed ({failure_count}/{self.max_failures})")
                if failure_count >= self.max_failures:
                    print("[NetCheck] Network lost. Triggering shutdown...")
                    self.on_failure()
                    break
            else:
                failure_count = 0
            time.sleep(self.check_interval)

    def _ping(self, ip):
        try:
            subprocess.check_output(["ping", "-c", "1", "-W", "1", ip], stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def stop(self):
        self._stop.set()
        self.thread.join(timeout=5)
