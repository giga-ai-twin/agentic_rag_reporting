import os
import json
from datetime import datetime

class FeedbackManager:
    """
    Manages user feedback storage and retrieval.
    Currently uses a JSON file, but can be easily swapped for a Database.
    """
    def __init__(self, feedback_file="feedback_log.json"):
        self.feedback_file = feedback_file

    def save_feedback(self, query, response, rating, comments=None):
        """
        Saves user feedback to the local storage.
        rating: 'positive' or 'negative'
        """
        entry = {
            "rating": rating,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "response": response,
            "comments": comments
        }

        # Load existing data or start fresh
        data = self._load_data()
        data.append(entry)
        self._save_data(data)

    def get_all_feedback(self):
        """Retrieves all stored feedback."""
        return self._load_data()

    def clear_log(self):
        """Clears the feedback history."""
        if os.path.exists(self.feedback_file):
            os.remove(self.feedback_file)

    def _load_data(self):
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def _save_data(self, data):
        with open(self.feedback_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)