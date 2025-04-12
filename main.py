import os
import sys
import logging
import threading
import datetime
import argparse

from adapters.live_sniffer import LiveSnifferAdapter
from adapters.pcap_replay import PCAPReplayAdapter
from adapters.suricata_alert_adapter import SuricataAlertAdapter
from adapters.hue_output import HueOutputAdapter
from adapters.music_output import MusicOutputAdapter
from adapters.console_output import ConsoleOutputAdapter
from core.core_processor import NetworkMonitorCore, NetworkConnectivityMonitor
from ui.ui import NetMonUI
from utils import create_veth_pair, delete_veth_pair, VETH_MAIN, VETH_PEER
import faulthandler
faulthandler.enable()

parser = argparse.ArgumentParser(description="Auracast Network Monitor")
parser.add_argument('--test', action='store_true', help='Enable testing mode (logs go to /var/log/netmon_sessions/testing)')
args = parser.parse_args()

IS_TESTING = args.test

# Config
PCAP_FILE_PATH = "/home/sparklefran/netmon4/pcap_files/2017-12-29-Dreambot-infection-traffic.pcap"
OUTPUT_DIR = "/var/log/suricata"
PHUE_IP_ADDRESS = "10.42.0.95"
LIGTHNAME = "fluxlight"
base_dir = "/var/log/netmon_sessions/testing" if IS_TESTING else "/var/log/netmon_sessions"

# Check if running as root; if not, re-run with sudo
if os.geteuid() != 0:
    print("Script is not running as root. Relaunching with sudo...")
    os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def build_output_adapters(mode):
    adapters = []
    if mode in ("visualisation", "both"):
        adapters.append(HueOutputAdapter(bridge_ip=PHUE_IP_ADDRESS, light_name=LIGTHNAME))
    if mode in ("sonification", "both"):
        adapters.append(MusicOutputAdapter())
    if mode == "none":
        return [ConsoleOutputAdapter()]  # fallback
    adapters.append(ConsoleOutputAdapter())
    return adapters

def start_traffic_adapter(mode, interface, shutdown_callback):
    if mode == "live":
        adapter = LiveSnifferAdapter(interface=interface)
    else:
        adapter = PCAPReplayAdapter(pcap_path=PCAP_FILE_PATH, interface=interface, on_complete=shutdown_callback)
    threading.Thread(target=adapter.start, args=(lambda pkt: None,), daemon=True).start()
    return adapter

def main():
    setup_logging()
    logging.info("Starting Network Monitor...")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(base_dir, f"session_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    alert_log_path = os.path.join(session_dir, "alert_log.txt")

    ui = NetMonUI(base_dir=base_dir)
    ui.run()  # Blocks exec until input/output mode selected

    input_mode = ui.choices["input"]
    output_mode = ui.choices["output"]
    interface = VETH_MAIN if input_mode == "pcap" else "wlo1"

    if input_mode == "pcap":
        create_veth_pair()

    def shutdown():
        print("[Main] PCAP replay finished. Initiating graceful shutdown.")
        ui.quit_app()

    shutdown_callback = shutdown if input_mode == "pcap" else None

    traffic_adapter = start_traffic_adapter(input_mode, interface, shutdown_callback=shutdown_callback)
    output_adapters = build_output_adapters(output_mode)

    core = None
    def core_callback(event):
        if core:
            core.process_event(event)
        with open(alert_log_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {event}\n")

    log_callback = ui.get_log_callback()

    suricata_adapter = SuricataAlertAdapter(
        interface=VETH_PEER if input_mode == "pcap" else interface,
        log_dir=OUTPUT_DIR,
        window_duration=5.0,
        callback=core_callback,
        rotate_interval=60,
        log_func=log_callback
    )

    core = NetworkMonitorCore(input_adapter=suricata_adapter, output_adapters=output_adapters)
    ui.set_core(core)

    core_thread = threading.Thread(target=core.start, daemon=True)
    core_thread.start()
    ui.core_thread = core_thread

    def network_failure_shutdown():
        log_callback("[Main] Network unreachable. Initiating shutdown.")
        ui.quit_app()

    net_monitor = NetworkConnectivityMonitor(on_failure=network_failure_shutdown)
    net_monitor.start()

    ui.root.mainloop()

    if hasattr(traffic_adapter, "stop"):
        traffic_adapter.stop()

    if core_thread.is_alive():
        core_thread.join(timeout=5)

    if input_mode == "pcap":
        delete_veth_pair()

    log_callback("[Main] Monitoring session ended.")

if __name__ == "__main__":
    main()
