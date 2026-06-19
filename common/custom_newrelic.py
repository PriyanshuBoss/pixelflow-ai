import newrelic.agent
import logging
logger = logging.getLogger(__name__)

class CustomNewRelic:
    @staticmethod
    def record_event(event_type, attributes=None):
        """
        Record a custom event to New Relic.

        Args:
            event_type (str): Name of the event type (e.g., 'ThemeExtractionSuccess').
            attributes (dict): Optional dictionary of custom attributes to send.
        """
        if not attributes:
            attributes = {}

        try:
            newrelic.agent.record_custom_event(event_type, attributes)

        except Exception as e:
            logger.warning(f"Failed to send New Relic event '{event_type}': {e}")
