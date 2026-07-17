import asyncio
from backend.src.agents.checkpoint_runtime import checkpoint_scope

async def main():
    async with checkpoint_scope() as checkpointer:
        print(dir(checkpointer))
        # Find a thread_id that exists
        
if __name__ == "__main__":
    asyncio.run(main())
