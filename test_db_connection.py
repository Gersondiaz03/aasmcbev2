import asyncio
import sys
import os
import traceback

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Print Python version and environment info
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment variables:")
for key, value in os.environ.items():
    if "DATABASE" in key or "SECRET" in key or "ALGORITHM" in key:
        print(f"  {key}: {'*' * min(len(value), 8)}...{value[-4:]}")

try:
    from dotenv import load_dotenv
    print("Loading .env file...")
    load_dotenv()
    print(".env file loaded")
except Exception as e:
    print(f"Error loading .env: {e}")

try:
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal, engine
    print("Successfully imported database modules")
except Exception as e:
    print(f"Error importing database modules: {e}")
    traceback.print_exc()
    sys.exit(1)

async def test_database_connection():
    print("\nTesting database connection...")
    
    try:
        # Test connection with engine
        print("Testing with engine.connect()...")
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Engine connection successful! Result: {result.scalar()}")
    except Exception as e:
        print(f"Engine connection failed with error: {e}")
        traceback.print_exc()
    
    try:
        # Test connection with AsyncSessionLocal
        print("\nTesting with AsyncSessionLocal()...")
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 2"))
            print(f"Session connection successful! Result: {result.scalar()}")
    except Exception as e:
        print(f"Session connection failed with error: {e}")
        traceback.print_exc()
        
    print("\nDatabase connection test completed")

if __name__ == "__main__":
    asyncio.run(test_database_connection())
