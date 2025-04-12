from scapy.all import sniff
from .input_adapter import InputAdapter

class LiveSnifferAdapter(InputAdapter):
    """
    Input adapter that captures live network traffic.
    This adapter is intended solely to feed network traffic (e.g. to Suricata IDS).
    """
    def __init__(self, interface: str, bpf_filter: str = None):
        self.interface = interface
        self.bpf_filter = bpf_filter
        self._stop = False

    def start(self, process_callback):
        print(f"[LiveSnifferAdapter] Starting live capture on {self.interface} with filter '{self.bpf_filter}'")
        sniff(iface=self.interface, filter=self.bpf_filter, prn=process_callback, stop_filter=lambda x: self._stop)

    def stop(self):
        self._stop = True
