import aiohttp
import os


async def give_forte_point(user_id: int, point: int) -> int:
    async with aiohttp.ClientSession(
        headers={
            "Authorization": os.getenv("FORTE_TOKEN"),
            "accept": "application/json",
        }
    ) as session:
        async with session.get(
            os.getenv("FORTE_BASE_URL") + f"/discords/{user_id}"
        ) as resp:
            user = await resp.json()
            if not user:
                raise ForteError(404, "사용자를 찾을 수 없습니다.")

        async with session.post(
            os.getenv("FORTE_BASE_URL") + f"/users/{user['id']}/points",
            json={"points": point},
        ) as resp:
            if resp.status not in (200, 201):
                raise ForteError(
                    resp.status, (await resp.json()).get("message", "Unknown Error")
                )

            return (await resp.json())["receipt_id"]


class ForteError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message

    def __str__(self) -> str:
        return f"<ForteError status={self.status}, message={self.message}>"
