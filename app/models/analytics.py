from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.extensions import db


class VisitorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(36), nullable=False, unique=True)
    last_seen = db.Column(db.DateTime, nullable=False, default=datetime.now(ZoneInfo("UTC")))

    __table_args__ = (db.Index('ix_visitorlog_last_seen', 'last_seen'),)


class WebhookDebugLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.now(ZoneInfo("UTC")))
    log_type = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    webhook_id = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<WebhookDebugLog {self.id} - {self.log_type}>"
