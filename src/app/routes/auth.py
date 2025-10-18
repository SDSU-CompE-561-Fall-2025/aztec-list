from fastapi import APIRouter

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@auth_router.post("/signup")
async def signup() -> dict[str, str]:
    return {"message": "Hello World"}


@auth_router.post("/login")
async def login() -> dict[str, str]:
    return {"message": "Hello World"}
