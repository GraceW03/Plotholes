from backend.database import db
from datetime import datetime

class BlockedEdges(db.Model):
    __tablename__ = 'blocked_edges'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    u = db.Column(db.BigInteger, nullable=False)  # start node
    v = db.Column(db.BigInteger, nullable=False)  # end node
    k = db.Column(db.BigInteger, default=0)       # edge key for parallel edges
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)