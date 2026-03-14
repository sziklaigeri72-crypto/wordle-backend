import logging
import random
import string
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.game_rooms import Game_rooms
from models.room_players import Room_players

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multiplayer", tags=["multiplayer"])


def generate_room_code() -> str:
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=5))


def generate_player_id() -> str:
    return "p_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))


# --- Request / Response Models ---

class CreateRoomRequest(BaseModel):
    player_name: str
    target_word: str

class CreateRoomResponse(BaseModel):
    room_code: str
    player_id: str

class JoinRoomRequest(BaseModel):
    player_name: str
    room_code: str

class JoinRoomResponse(BaseModel):
    room_code: str
    player_id: str
    target_word: str
    game_started: bool

class StartGameRequest(BaseModel):
    room_code: str
    player_id: str

class GuessRequest(BaseModel):
    room_code: str
    player_id: str
    guess_count: int
    solved: bool
    failed: bool

class PollRequest(BaseModel):
    room_code: str
    player_id: str

class PlayerOut(BaseModel):
    id: str
    name: str
    guesses: int
    solved: bool
    failed: bool
    total_score: int

class PollResponse(BaseModel):
    room_code: str
    status: str
    game_started: bool
    target_word: Optional[str] = None
    players: list[PlayerOut]
    winner_id: Optional[str] = None
    winner_name: Optional[str] = None
    is_host: bool
    current_round: int
    max_rounds: int

class LeaveRequest(BaseModel):
    room_code: str
    player_id: str

class NewRoundRequest(BaseModel):
    room_code: str
    player_id: str
    target_word: str


# --- Endpoints ---

@router.post("/create_room", response_model=CreateRoomResponse)
async def create_room(data: CreateRoomRequest, db: AsyncSession = Depends(get_db)):
    """Create a new game room."""
    player_id = generate_player_id()
    room_code = generate_room_code()

    # Ensure unique room code
    for _ in range(10):
        existing = await db.execute(
            select(Game_rooms).where(Game_rooms.room_code == room_code)
        )
        if existing.scalar_one_or_none() is None:
            break
        room_code = generate_room_code()

    now = datetime.now()
    room = Game_rooms(
        room_code=room_code,
        target_word=data.target_word,
        host_player_id=player_id,
        game_started=False,
        status="waiting",
        created_at=now,
    )
    db.add(room)
    await db.flush()

    player = Room_players(
        room_id=room.id,
        player_id=player_id,
        player_name=data.player_name,
        guesses=0,
        solved=False,
        failed=False,
        last_seen=now,
    )
    db.add(player)
    await db.commit()

    return CreateRoomResponse(room_code=room_code, player_id=player_id)


@router.post("/join_room", response_model=JoinRoomResponse)
async def join_room(data: JoinRoomRequest, db: AsyncSession = Depends(get_db)):
    """Join an existing game room."""
    result = await db.execute(
        select(Game_rooms).where(Game_rooms.room_code == data.room_code.upper())
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="A szoba nem található!")
    if room.status == "finished":
        raise HTTPException(status_code=400, detail="Ez a játék már véget ért!")

    # Count players
    players_result = await db.execute(
        select(Room_players).where(Room_players.room_id == room.id)
    )
    players = players_result.scalars().all()
    if len(players) >= 8:
        raise HTTPException(status_code=400, detail="A szoba megtelt! (max 8 játékos)")

    player_id = generate_player_id()
    now = datetime.now()
    player = Room_players(
        room_id=room.id,
        player_id=player_id,
        player_name=data.player_name,
        guesses=0,
        solved=False,
        failed=False,
        last_seen=now,
    )
    db.add(player)
    await db.commit()

    return JoinRoomResponse(
        room_code=room.room_code,
        player_id=player_id,
        target_word=room.target_word,
        game_started=room.game_started or False,
    )


@router.post("/start_game")
async def start_game(data: StartGameRequest, db: AsyncSession = Depends(get_db)):
    """Start the game (host only)."""
    result = await db.execute(
        select(Game_rooms).where(Game_rooms.room_code == data.room_code)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Szoba nem található!")
    if room.host_player_id != data.player_id:
        raise HTTPException(status_code=403, detail="Csak a szoba gazdája indíthatja a játékot!")

    room.game_started = True
    room.status = "playing"
    await db.commit()
    return {"ok": True}


@router.post("/guess")
async def submit_guess(data: GuessRequest, db: AsyncSession = Depends(get_db)):
    """Submit a guess result."""
    result = await db.execute(
        select(Game_rooms).where(Game_rooms.room_code == data.room_code)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Szoba nem található!")

    # Find player
    player_result = await db.execute(
        select(Room_players).where(
            and_(Room_players.room_id == room.id, Room_players.player_id == data.player_id)
        )
    )
    player = player_result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Játékos nem található!")

    player.guesses = data.guess_count
    player.solved = data.solved
    player.failed = data.failed
    player.last_seen = datetime.now()

    # If solved and no winner yet, set winner
    if data.solved and not room.winner_player_id:
        room.winner_player_id = data.player_id
        room.winner_name = player.player_name

    # Check if all players are done
    all_players_result = await db.execute(
        select(Room_players).where(Room_players.room_id == room.id)
    )
    all_players = all_players_result.scalars().all()
    all_done = all(p.solved or p.failed for p in all_players)
    if all_done:
        room.status = "round_over"

    await db.commit()
    return {"ok": True}


@router.post("/poll", response_model=PollResponse)
async def poll_room(data: PollRequest, db: AsyncSession = Depends(get_db)):
    """Poll room state for updates."""
    result = await db.execute(
        select(Game_rooms).where(Game_rooms.room_code == data.room_code)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Szoba nem található!")

    # Update last_seen for this player
    player_result = await db.execute(
        select(Room_players).where(
            and_(Room_players.room_id == room.id, Room_players.player_id == data.player_id)
        )
    )
    player = player_result.scalar_one_or_none()
    if player:
        player.last_seen = datetime.now()
        await db.commit()

    # Get all players
    all_players_result = await db.execute(
        select(Room_players).where(Room_players.room_id == room.id)
    )
    all_players = all_players_result.scalars().all()

    players_out = [
        PlayerOut(
            id=p.player_id,
            name=p.player_name,
            guesses=p.guesses or 0,
            solved=p.solved or False,
            failed=p.failed or False,
            total_score=p.total_score or 0,
        )
        for p in all_players
    ]

    is_host = room.host_player_id == data.player_id

    return PollResponse(
        room_code=room.room_code,
        status=room.status or "waiting",
        game_started=room.game_started or False,
        target_word=room.target_word,
        players=players_out,
        winner_id=room.winner_player_id,
        winner_name=room.winner_name,
        is_host=is_host,
        current_round=room.current_round or 1,
        max_rounds=5,
    )


@router.post("/new_round")
async def new_round(data: NewRoundRequest, db: AsyncSession = Depends(get_db)):
    """Start a new round (host only). Resets player guesses but keeps total scores."""
    result = await db.execute(
        select(Game_rooms).where(Game_rooms.room_code == data.room_code)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Szoba nem található!")
    if room.host_player_id != data.player_id:
        raise HTTPException(status_code=403, detail="Csak a szoba gazdája indíthat új kört!")

    current_round = room.current_round or 1
    if current_round >= 5:
        room.status = "finished"
        await db.commit()
        return {"ok": True, "finished": True}

    # Calculate round scores and add to total_score
    all_players_result = await db.execute(
        select(Room_players).where(Room_players.room_id == room.id)
    )
    all_players = all_players_result.scalars().all()

    for p in all_players:
        round_score = 0
        if p.solved:
            round_score = max(0, (7 - (p.guesses or 0)) * 100)
        current_total = p.total_score or 0
        p.total_score = current_total + round_score
        # Reset round state
        p.guesses = 0
        p.solved = False
        p.failed = False

    # Update room for new round
    room.current_round = current_round + 1
    room.target_word = data.target_word
    room.winner_player_id = None
    room.winner_name = None
    room.status = "playing"
    room.game_started = True

    await db.commit()
    return {"ok": True, "finished": False, "round": current_round + 1}


@router.post("/leave")
async def leave_room(data: LeaveRequest, db: AsyncSession = Depends(get_db)):
    """Leave a room."""
    result = await db.execute(
        select(Game_rooms).where(Game_rooms.room_code == data.room_code)
    )
    room = result.scalar_one_or_none()
    if not room:
        return {"ok": True}

    # Remove player
    player_result = await db.execute(
        select(Room_players).where(
            and_(Room_players.room_id == room.id, Room_players.player_id == data.player_id)
        )
    )
    player = player_result.scalar_one_or_none()
    if player:
        await db.delete(player)
        await db.commit()

    # Check if room is empty
    remaining = await db.execute(
        select(Room_players).where(Room_players.room_id == room.id)
    )
    if not remaining.scalars().first():
        await db.delete(room)
        await db.commit()

    return {"ok": True}