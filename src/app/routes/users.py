from fastapi import APIRouter

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@user_router.get("/{user_id}")
async def get_user(user_id: int) -> dict[str, str]:
    return {"message": f"Hello {user_id}"}
