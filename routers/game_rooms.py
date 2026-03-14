import json
import logging
from typing import List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.game_rooms import Game_roomsService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/game_rooms", tags=["game_rooms"])


# ---------- Pydantic Schemas ----------
class Game_roomsData(BaseModel):
    """Entity data schema (for create/update)"""
    room_code: str
    target_word: str
    host_player_id: str
    game_started: bool = None
    winner_player_id: str = None
    winner_name: str = None
    status: str
    current_round: int = None
    created_at: Optional[datetime] = None


class Game_roomsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    room_code: Optional[str] = None
    target_word: Optional[str] = None
    host_player_id: Optional[str] = None
    game_started: Optional[bool] = None
    winner_player_id: Optional[str] = None
    winner_name: Optional[str] = None
    status: Optional[str] = None
    current_round: Optional[int] = None
    created_at: Optional[datetime] = None


class Game_roomsResponse(BaseModel):
    """Entity response schema"""
    id: int
    room_code: str
    target_word: str
    host_player_id: str
    game_started: Optional[bool] = None
    winner_player_id: Optional[str] = None
    winner_name: Optional[str] = None
    status: str
    current_round: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Game_roomsListResponse(BaseModel):
    """List response schema"""
    items: List[Game_roomsResponse]
    total: int
    skip: int
    limit: int


class Game_roomsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Game_roomsData]


class Game_roomsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Game_roomsUpdateData


class Game_roomsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Game_roomsBatchUpdateItem]


class Game_roomsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Game_roomsListResponse)
async def query_game_roomss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query game_roomss with filtering, sorting, and pagination"""
    logger.debug(f"Querying game_roomss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Game_roomsService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} game_roomss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying game_roomss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Game_roomsListResponse)
async def query_game_roomss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query game_roomss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying game_roomss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Game_roomsService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} game_roomss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying game_roomss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Game_roomsResponse)
async def get_game_rooms(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single game_rooms by ID"""
    logger.debug(f"Fetching game_rooms with id: {id}, fields={fields}")
    
    service = Game_roomsService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Game_rooms with id {id} not found")
            raise HTTPException(status_code=404, detail="Game_rooms not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game_rooms {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Game_roomsResponse, status_code=201)
async def create_game_rooms(
    data: Game_roomsData,
    db: AsyncSession = Depends(get_db),
):
    """Create a new game_rooms"""
    logger.debug(f"Creating new game_rooms with data: {data}")
    
    service = Game_roomsService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create game_rooms")
        
        logger.info(f"Game_rooms created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating game_rooms: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating game_rooms: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Game_roomsResponse], status_code=201)
async def create_game_roomss_batch(
    request: Game_roomsBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple game_roomss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} game_roomss")
    
    service = Game_roomsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} game_roomss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Game_roomsResponse])
async def update_game_roomss_batch(
    request: Game_roomsBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update multiple game_roomss in a single request"""
    logger.debug(f"Batch updating {len(request.items)} game_roomss")
    
    service = Game_roomsService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} game_roomss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Game_roomsResponse)
async def update_game_rooms(
    id: int,
    data: Game_roomsUpdateData,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing game_rooms"""
    logger.debug(f"Updating game_rooms {id} with data: {data}")

    service = Game_roomsService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Game_rooms with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Game_rooms not found")
        
        logger.info(f"Game_rooms {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating game_rooms {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating game_rooms {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_game_roomss_batch(
    request: Game_roomsBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple game_roomss by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} game_roomss")
    
    service = Game_roomsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} game_roomss successfully")
        return {"message": f"Successfully deleted {deleted_count} game_roomss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_game_rooms(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single game_rooms by ID"""
    logger.debug(f"Deleting game_rooms with id: {id}")
    
    service = Game_roomsService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Game_rooms with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Game_rooms not found")
        
        logger.info(f"Game_rooms {id} deleted successfully")
        return {"message": "Game_rooms deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting game_rooms {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")