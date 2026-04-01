from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from database.models import User, History, Watchlist
import logging

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, user_id: int, full_name: str, username: str):
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            user = User(user_id=user_id, full_name=full_name, username=username)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        else:
            # Foydalanuvchi ma'lumotlari o'zgargan bo'lsa yangilaymiz
            if user.full_name != full_name or user.username != username:
                user.full_name = full_name
                user.username = username
                await self.session.commit()
                await self.session.refresh(user)
        return user

    async def get_total_users_count(self):
        query = select(func.count(User.id))
        result = await self.session.execute(query)
        return result.scalar()

    async def add_history(self, user_db_id: int, movie_id: int):
        new_history = History(user_id=user_db_id, movie_id=movie_id)
        self.session.add(new_history)
        await self.session.commit()

    async def get_user_history(self, user_db_id: int, limit: int = 10, offset: int = 0):
        # Oxirgi ko'rilganlar birinchi, kino ma'lumotlari bilan birga
        query = select(History).options(joinedload(History.movie)).where(History.user_id == user_db_id).order_by(History.viewed_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_watchlist(self, user_db_id: int):
        query = select(Watchlist).options(joinedload(Watchlist.movie)).where(Watchlist.user_id == user_db_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def remove_from_watchlist(self, user_db_id: int, movie_id: int):
        query = select(Watchlist).where(Watchlist.user_id == user_db_id, Watchlist.movie_id == movie_id)
        result = await self.session.execute(query)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()
            return True
        return False

    async def set_admin(self, user_id: int, status: bool = True):
        query = select(User).where(User.user_id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            user.is_admin = status
            await self.session.commit()
            return True
        return False

    async def is_admin(self, user_id: int):
        # Env dagi ADMIN_ID ni ham tekshirish (Super admin)
        import os
        if user_id == int(os.getenv("ADMIN_ID", 0)):
            return True
        
        query = select(User).where(User.user_id == user_id, User.is_admin == True)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_all_admins(self):
        query = select(User).where(User.is_admin == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_user_ids(self):
        query = select(User.user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
