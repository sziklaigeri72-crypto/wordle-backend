from core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Game_rooms(Base):
    __tablename__ = "game_rooms"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    room_code = Column(String, nullable=False)
    target_word = Column(String, nullable=False)
    host_player_id = Column(String, nullable=False)
    game_started = Column(Boolean, nullable=True)
    winner_player_id = Column(String, nullable=True)
    winner_name = Column(String, nullable=True)
    status = Column(String, nullable=False)
    current_round = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)