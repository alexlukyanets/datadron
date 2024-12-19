from asyncio import Runner


async def main():
    ...


if __name__ == '__main__':
    with Runner() as runner:
        runner.run(main())
