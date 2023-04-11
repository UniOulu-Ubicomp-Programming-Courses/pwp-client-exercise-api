import hashlib
import secrets
from . import db


cert_schema = {
    "type": "object",
    "required": ["group", "certificate", "generated"],
    "properties": {
        "group": {
            "type": "string",
            "description": "Group handle",
        },
        "certificate": {
            "type": "string",
            "description": "Generated certificate",
        },
        "generated": {
            "type": "string",
            "description": "Generation timestamp",
            "format": "date-time",
        }
    },
}


class Group(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(32), unique=True, nullable=False)
    name= db.Column(db.String(128), nullable=True)
    salt = db.Column(db.String(16), unique=True, nullable=False)

    api_key = db.relationship("ApiKey", cascade="all, delete-orphan", back_populates="group", uselist=False)

    @staticmethod
    def json_schema() -> dict:
        props = {}
        props["name"] = {
            "description": "Group name as written by the group",
            "type": "string",
            "maxLength": 128,
        }
        props["handle"] = {
            "description": "Group handle used by course services",
            "type": "string",
            "maxLength": 32
        }
        props["salt"] = {
            "description": "Salt string that is used when generating and validating submissions",
            "type": "string",
            "maxLength": 16,
        }
        return {
            "type": "object",
            "required": ["handle", "salt"],
            "properties": props
        }

    def serialize(self):
        return {
            "handle": self.handle,
            "name": self.name,
            "salt": self.salt
        }

    def deserialize(self, data):
        self.handle = data["handle"]
        self.name = data.get("name", "")
        self.salt = data["salt"]


class ApiKey(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.ForeignKey("group.id", ondelete="CASCADE"), nullable=True, unique=True)
    key = db.Column(db.String(32), nullable=False, unique=True)
    admin = db.Column(db.Boolean, default=False)
    group = db.relationship("Group", back_populates="api_key", uselist=False)

    @staticmethod
    def key_hash(key):
        return hashlib.sha256(key.encode()).digest()

    @staticmethod
    def generate():
        return secrets.token_urlsafe()


