from httpx import AsyncClient


class DataDroneClient:
    def __init__(self):
        self.client: AsyncClient = AsyncClient()

    async def request(self, method: str, url: str, **kwargs):
        return await self.client.request(method, url, **kwargs)
