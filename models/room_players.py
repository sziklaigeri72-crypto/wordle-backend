from core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Room_players(Base):
    __tablename__ = "room_players"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    room_id = Column(Integer, nullable=False)
    player_id = Column(String, nullable=False)
    player_name = Column(String, nullable=False)
    guesses = Column(Integer, nullable=True)
    solved = Column(Boolean, nullable=True)
    failed = Column(Boolean, nullable=True)
    total_score = Column(Integer, nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)