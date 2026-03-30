from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import BotSetting

class SettingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_setting(self, key: str, default=None):
        query = select(BotSetting.value).where(BotSetting.key == key)
        result = await self.session.execute(query)
        val = result.scalar_one_or_none()
        return val if val is not None else default

    async def set_setting(self, key: str, value: str):
        query = select(BotSetting).where(BotSetting.key == key)
        result = await self.session.execute(query)
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
        else:
            setting = BotSetting(key=key, value=value)
            self.session.add(setting)
        
        await self.session.commit()
        return setting
