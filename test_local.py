import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.app import run_pipeline

async def main():
    try:
        r1, r2 = await asyncio.gather(
            run_pipeline("Aspirin", "en"),
            run_pipeline("Metformin", "en")
        )
        print("Success")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
