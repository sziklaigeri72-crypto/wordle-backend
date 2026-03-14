import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.room_players import Room_players

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class Room_playersService:
    """Service layer for Room_players operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Room_players]:
        """Create a new room_players"""
        try:
            obj = Room_players(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created room_players with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating room_players: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Room_players]:
        """Get room_players by ID"""
        try:
            query = select(Room_players).where(Room_players.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching room_players {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of room_playerss"""
        try:
            query = select(Room_players)
            count_query = select(func.count(Room_players.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Room_players, field):
                        query = query.where(getattr(Room_players, field) == value)
                        count_query = count_query.where(getattr(Room_players, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Room_players, field_name):
                        query = query.order_by(getattr(Room_players, field_name).desc())
                else:
                    if hasattr(Room_players, sort):
                        query = query.order_by(getattr(Room_players, sort))
            else:
                query = query.order_by(Room_players.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching room_players list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Room_players]:
        """Update room_players"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Room_players {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated room_players {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating room_players {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete room_players"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Room_players {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted room_players {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting room_players {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Room_players]:
        """Get room_players by any field"""
        try:
            if not hasattr(Room_players, field_name):
                raise ValueError(f"Field {field_name} does not exist on Room_players")
            result = await self.db.execute(
                select(Room_players).where(getattr(Room_players, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching room_players by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Room_players]:
        """Get list of room_playerss filtered by field"""
        try:
            if not hasattr(Room_players, field_name):
                raise ValueError(f"Field {field_name} does not exist on Room_players")
            result = await self.db.execute(
                select(Room_players)
                .where(getattr(Room_players, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Room_players.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching room_playerss by {field_name}: {str(e)}")
            raise