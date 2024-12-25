from asyncio import gather

from logger import logger
from config import settings

from core.client.client import DataDroneClient


async def test_client(client: DataDroneClient, url: str, sync: bool = False, times: int = 50):
    if sync:
        await gather(*[client.get(url=url) for _ in range(times)])
    else:
        for _ in range(times):
            await client.get(url=url)
    logger.success(f'Statistics: {await client.statistics()}')


async def drone_test():
    client: DataDroneClient = DataDroneClient(follow_redirects=True, logger_debug=True)
    for url in settings.TEST_URL_1, settings.TEST_URL_2:
        await test_client(client=client, url=url)
