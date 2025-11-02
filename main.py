import asyncio
import datetime

import flights


async def amain():
    explorer = flights.FlightFinder()
    await explorer.init()
    results = explorer.search(
        {
            "currency": "EUR",
            "destination": "GVA",
            "origin": "LIS",
            "return_journey": False,
            "start_date": datetime.date(2026, 2, 1),
            "end_date": datetime.date(2026, 2, 5),
        }
    )
    async for obj in results:
        print("obj", obj)
    await explorer.close()

def main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(asyncio.wait_for(amain(), None))
    loop.close()

if __name__ == "__main__":
    main()
