import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.model_router import model_router


async def main() -> None:
    result = await model_router.rewrite_script("今天给大家分享一个提升短视频口播效率的方法。")
    print(
        {
            "model": result["model"],
            "script_len": len(result["rewritten_script"]),
            "segments": len(result["segments"]),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
