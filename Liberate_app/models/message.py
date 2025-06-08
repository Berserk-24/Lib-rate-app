from datetime import datetime

class Message:
    def __init__(self, message_id, sender_id, receiver_id, content, timestamp=None, location=None):
        self.message_id = message_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.location = location  # Puede ser un dict con lat/lon

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "location": self.location
        }