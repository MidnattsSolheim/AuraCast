import time
from scapy.all import rdpcap, sendp
from .input_adapter import InputAdapter

class PCAPReplayAdapter(InputAdapter):
    """
    Input adapter that replays packets from a PCAP file using Scapy.
    Suitable for low-volume, controlled replay on any interface (including Wi-Fi).
    """
    def __init__(self, pcap_path: str, interface: str = None, interval: float = 0, on_complete=None):
        self.pcap_path = pcap_path
        self.interface = interface
        self.interval = interval
        self._stop = False
        self.on_complete = on_complete

    def start(self, process_callback):
        print(f"[PCAPReplayAdapter] Replaying packets from {self.pcap_path} with interval {self.interval}s")
        self._stop = False
        try:
            packets = rdpcap(self.pcap_path)
            for pkt in packets:
                if self._stop:
                    break
                process_callback(pkt)
                sendp(pkt, iface=self.interface, verbose=False)
                if self.interval > 0:
                    time.sleep(self.interval)
            if self.on_complete:
                self.on_complete()
        except Exception as e:
            print(f"[PCAPReplayAdapter] Error replaying PCAP with Scapy: {e}")

    def stop(self):
        print("[PCAPReplayAdapter] Stop requested.")
        self._stop = True
