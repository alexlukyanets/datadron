from asyncio import Runner

from tests.client_test import drone_test


async def main():
    await drone_test()


if __name__ == '__main__':
    with Runner() as runner:
        runner.run(main())
