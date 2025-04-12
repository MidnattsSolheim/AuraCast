from .output_adapter import OutputAdapter

class ConsoleOutputAdapter(OutputAdapter):
    """
    Output adapter that logs events to the console.
    If an event includes an aggregated alert count, it logs that.
    """
    def handle_event(self, event):
        alert = event.get("alert", {})
        if alert.get("severity") == 1:
            category = alert.get("category", "Unknown Category")
            severity = alert.get("severity")
            print(f"[ConsoleOutputAdapter] Severity: {severity}\nCategory: {category}")
        elif "aggregated_alert_count" in event:
            count = event["aggregated_alert_count"]
            print(f"[ConsoleOutputAdapter] Aggregated Alert Count: {count}")
