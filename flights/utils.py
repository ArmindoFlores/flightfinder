import asyncio
import typing

T = typing.TypeVar("T")
async def as_completed_limited(n: int, coroutines: typing.Iterable[asyncio.Future[T]]) -> typing.AsyncGenerator[T | Exception, None]:
    it = iter(coroutines)
    running = set()

    for _ in range(n):
        try:
            c = next(it)
        except StopIteration:
            break
        running.add(asyncio.create_task(c))

    try:
        while running:
            done, running = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)

            for t in done:
                try:
                    yield await t
                except Exception as e:
                    yield e

                try:
                    c = next(it)
                except StopIteration:
                    continue
                running.add(asyncio.create_task(c))
    finally:
        for t in running:
            t.cancel()
        await asyncio.gather(*running, return_exceptions=True)
