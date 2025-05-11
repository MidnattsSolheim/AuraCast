import os
import time
import json
import threading
import subprocess
from .input_adapter import InputAdapter
import math

from datetime import datetime

def format_alert_summary(event):
    alert = event.get("alert", {})
    src_ip = event.get("src_ip", "unknown")
    src_port = event.get("src_port", "?")
    dest_ip = event.get("dest_ip", "unknown")
    dest_port = event.get("dest_port", "?")
    signature = alert.get("signature", "No description")
    severity = alert.get("severity", 3)
    timestamp_raw = event.get("timestamp", None)

    if timestamp_raw:
        try:
            timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            timestamp = "unknown time"
    else:
        timestamp = "unknown time"

    level = {
        1: "[HIGH]",
        2: "[MEDIUM]",
        3: "[LOW]"
    }.get(severity, "[INFO]")

    return f"{timestamp} {level} {signature} from {src_ip}:{src_port} → {dest_ip}:{dest_port}"

class SuricataAlertAdapter(InputAdapter):
    def __init__(self, interface: str, log_dir: str, window_duration=5.0, callback=None, rotate_interval=None, log_func=None):
        self.interface = interface
        self.log_dir = log_dir
        self.log_path = os.path.join(log_dir, "eve.json")
        self.window_duration = window_duration
        self.callback = callback
        self.rotate_interval = rotate_interval
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.suricata_proc = None
        self.log_func = log_func or (lambda msg: print(f"[SuricataAlertAdapter] {msg}"))
        self._last_alert_count = None

    def run_suricata(self):
        print("[SuricataAlertAdapter] Starting Suricata...")
        suricata_cmd = [
            "sudo", "suricata",
            "-i", self.interface,
            "-l", self.log_dir,
            "--set", "stream.reassembly.depth=0",
            "--set", "threading.cpu_affinity=0",
            "--set", "threading.detect-thread-ratio=1.0"
        ]
        return subprocess.Popen(suricata_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def start(self, process_callback=None):
        self.suricata_proc = self.run_suricata()
        self._prepare_file()
        self.thread.start()
        self.log_func("Starting Suricata...")
        print("[SuricataAlertAdapter] Started log monitoring.")

    def _prepare_file(self):
        self.log_func("Preparing Suricata log file...")
        while not os.path.exists(self.log_path) and not self._stop.is_set():
            time.sleep(0.5)
        try:
            os.chmod(self.log_path, 0o666)
            print("[SuricataAlertAdapter] Set permissions on eve.json to 666.")
        except Exception as e:
            print(f"[SuricataAlertAdapter] Warning: couldn't set permissions: {e}")
        try:
            with open(self.log_path, "w") as f:
                f.truncate(0)
            print("[SuricataAlertAdapter] Cleared eve.json at startup.")
        except Exception as e:
            print(f"[SuricataAlertAdapter] Error clearing eve.json: {e}")
    def _monitor_loop(self):
        severity_weights = {1: 9, 3: 2, 3: 1}
        alert_count = 0
        total_weighted_severity = 0
        contains_high_severity = False
        window_start = time.time()
        last_rotation = time.time()
        print("[SuricataAlertAdapter] Launching monitor loop")

        def open_log_file():
            f = open(self.log_path, "r")
            f.seek(0, os.SEEK_END)
            return f

        try:
            f = open_log_file()
            while not self._stop.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event_type") == "alert":
                    self.log_func(format_alert_summary(event))
                    severity = event.get("alert", {}).get("severity", 3)
                    if severity == 1:
                        contains_high_severity = True  # Flag it!
                    if severity in severity_weights:
                        total_weighted_severity += severity_weights[severity]
                        alert_count += 1


                now = time.time()
                
                if alert_count > 0:
                    average_severity_score = total_weighted_severity / alert_count
                else:
                    average_severity_score = 0
                volume_modifier = math.log1p(alert_count) / math.log1p(100)
                final_score = average_severity_score + volume_modifier

                if now - window_start >= self.window_duration:
                    if alert_count == 0:
                        if self._last_alert_count != 0:
                            self.log_func("[Suricata] Listening to traffic...")
                    if self.callback:
                         aggregated_event = {
                            "alert_score": final_score,
                            "alert_count": alert_count,
                            "average_severity": average_severity_score,
                            "volume_modifier": volume_modifier,
                            "contains_high_severity": contains_high_severity
                        }
                    self.callback(aggregated_event)
                    self._last_alert_count = alert_count
                    alert_count = 0
                    total_weighted_severity = 0
                    contains_high_severity = False
                    window_start = now

                if self.rotate_interval and now - last_rotation >= self.rotate_interval:
                    try:
                        f.close()
                        with open(self.log_path, "w") as rotate_f:
                            rotate_f.truncate(0)
                        print("[SuricataAlertAdapter] Rotated (cleared) eve.json.") # To ensure no log accumulation

                        # Reopen the file after rotating
                        f = open_log_file()
                    except Exception as e:
                        print(f"[SuricataAlertAdapter] Error rotating eve.json: {e}")
                    last_rotation = now

        except Exception as e:
            print(f"[SuricataAlertAdapter] Monitoring loop encountered an error: {e}")

    
    def stop(self):
        print("[SuricataAlertAdapter] Stopping log monitoring...")
        self._stop.set()
        self.thread.join()
        if self.suricata_proc:
            self.suricata_proc.terminate()
            self.suricata_proc.wait()
        print("[SuricataAlertAdapter] Suricata process terminated and monitoring stopped.")
        self.log_func("Stopping Suricata and monitoring...")
