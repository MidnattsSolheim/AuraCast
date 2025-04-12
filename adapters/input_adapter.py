class InputAdapter:
    """
    Abstract base class for network input adapters.
    Subclasses must implement start(process_callback) and stop() if applicable.
    """
    def start(self, process_callback):
        raise NotImplementedError("Subclasses must implement start()")
    
    def stop(self):
        pass
