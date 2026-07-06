import os, asyncio, json
import aiohttp
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

cid = os.environ.get("FATSECRET_CLIENT_ID", "")
cs = os.environ.get("FATSECRET_CLIENT_SECRET", "")

print(f"Client ID = [{cid}]")
print(f"Secret = [{cs[:6]}...{cs[-4:]}]")

async def main():
    # Step 1: get token
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://oauth.fatsecret.com/connect/token",
            data={"grant_type": "client_credentials", "scope": "basic"},
            auth=aiohttp.BasicAuth(cid, cs),
        ) as resp:
            print(f"Token status: {resp.status}")
            body = await resp.text()
            print(f"Token body: {body[:400]}")
            if resp.status != 200:
                return
            token = json.loads(body).get("access_token")

    # Step 2: search
    async with aiohttp.ClientSession() as session:
        params = {"method": "foods.search", "search_expression": "beef", "format": "json", "max_results": 3}
        async with session.get(
            "https://platform.fatsecret.com/rest/server.api",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        ) as resp:
            print(f"Search status: {resp.status}")
            print(f"Search body: {(await resp.text())[:2000]}")

asyncio.run(main())
