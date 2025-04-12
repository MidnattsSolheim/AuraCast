import time
import threading
from phue import Bridge
from .output_adapter import OutputAdapter

class HueOutputAdapter(OutputAdapter):
    DEFAULT_BRIDGE_IP = "10.42.0.95" # Hardcoded for the purposes of the PoC
    DEFAULT_LIGHT_NAME = "fluxlight"

    SMOOTH_STEPS = 20
    SMOOTH_DELAY = 0.1  # delay in seconds

    COLORS = {
        "green":  [0.31, 0.51],
        "orange": [0.561, 0.404],
        "yellow": [0.4448, 0.4066],
        "red":    [0.675, 0.322],
        "purple": [0.272, 0.109]
    }

    BRIGHTNESS = {
        "green":  150,
        "orange": 200,
        "red":    254,
        "purple": 200,
        "yellow": 180
    }


    def __init__(self, bridge_ip: str = None, light_name: str = None):
        self.bridge_ip = bridge_ip or self.DEFAULT_BRIDGE_IP
        self.light_name = light_name or self.DEFAULT_LIGHT_NAME
        self.bridge = None
        self.light = None
        self._stop_event = threading.Event()
        self.thread = None
        self.event_queue = []
        self.lock = threading.Lock()
        self._connected = False
        self._start_worker()

    def _connect_bridge(self):
        try:
            self.bridge = Bridge(self.bridge_ip)
            self.bridge.connect()
            lights = self.bridge.get_light_objects('name')
            if self.light_name in lights:
                self.light = lights[self.light_name]
                self._connected = True
                print(f"[HueOutputAdapter] Connected to bridge at {self.bridge_ip} and found light '{self.light_name}'.")
            else:
                print(f"[HueOutputAdapter] Light '{self.light_name}' not found.")
        except Exception as e:
            print(f"[HueOutputAdapter] Error connecting to bridge: {e}")
            self._connected = False

    def _start_worker(self):
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def _worker_loop(self):
        self._connect_bridge()
        while not self._stop_event.is_set():
            if not self._connected:
                self._connect_bridge()
                time.sleep(3)
                continue
            if self.event_queue:
                with self.lock:
                    event = self.event_queue.pop(0)
                self._process_event(event)
            time.sleep(0.1)

    def handle_event(self, event):
        with self.lock:
            self.event_queue.append(event)

    def _process_event(self, event):
        if self.light is None:
            print("[HueOutputAdapter] No light available; skipping event.")
            return
        final_score = event.get("alert_score", 0)
        print(f"[HueOutputAdapter] Processing alert score: {final_score}")
        if final_score >= 9:
            colour = "purple"   # very high severity or massive volume
        elif final_score >= 6:
            colour = "red"      # high severity or steady volume
        elif final_score >= 4:
            colour = "orange"   # elevated risk
        elif final_score >= 2:
            colour = "yellow"   # mild concern
        else:
            colour = "green"    # quiet baseline; shows the lights are working

        if final_score > 6 and event.get("contains_high_severity"):
            colour = "red"
            print("[HueOutputAdapter] High-severity alert present. Overriding to red.")

        target_xy = self.COLORS[colour]
        target_brightness = self.BRIGHTNESS[colour]
        print(f"[HueOutputAdapter] Setting light to {colour} (xy: {target_xy}, bri: {target_brightness})")
        self._smooth_light_transition(self.light, target_xy, target_brightness)

    def _smooth_light_transition(self, light, target_xy, target_brightness):
        try:
            # Light health check
            light.on = True

            current_xy = light.xy
            current_brightness = light.brightness
        except Exception as e:
            print(f"[HueOutputAdapter] Error retrieving current light state: {e}")
            self._connected = False
            return

        for step in range(self.SMOOTH_STEPS):
            if self._stop_event.is_set():
                break

            try:
                factor = step / self.SMOOTH_STEPS
                new_xy = [
                    current_xy[0] + (target_xy[0] - current_xy[0]) * factor,
                    current_xy[1] + (target_xy[1] - current_xy[1]) * factor
                ]
                new_bri = int(current_brightness + (target_brightness - current_brightness) * factor)

                # Sanity checks to avoid invalid values
                new_xy[0] = min(max(new_xy[0], 0.0), 1.0)
                new_xy[1] = min(max(new_xy[1], 0.0), 1.0)
                new_bri = min(max(new_bri, 1), 254)

                light.xy = new_xy
                time.sleep(0.02)  # Prevent overloading the bridge API - without it, the bridge crashes
                light.brightness = new_bri
            except Exception as e:
                print(f"[HueOutputAdapter] Error setting light state (xy={new_xy}, bri={new_bri}): {e}")
                self._connected = False
                break

            time.sleep(self.SMOOTH_DELAY)


    def stop(self):
        print("[HueOutputAdapter] Stopping and cleaning up.")
        colour = "green"
        target_xy = self.COLORS[colour]
        target_brightness = self.BRIGHTNESS[colour]
        self._smooth_light_transition(self.light, target_xy, target_brightness)
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.event_queue.clear()
        
        print("[HueOutputAdapter] Shutdown complete.")