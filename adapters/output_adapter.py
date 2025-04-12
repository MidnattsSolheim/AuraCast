class OutputAdapter:
    """
    Abstract base class for output adapters.
    Subclasses must implement handle_event(event).
    """
    def handle_event(self, event):
        raise NotImplementedError("Subclasses must implement handle_event()")
