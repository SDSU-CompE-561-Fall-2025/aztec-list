from pydantic import BaseModel


class ListingBase(BaseModel):
    title: str
    price: float


class ListingCreate(ListingBase):
    description: str


class ListingUpdate(BaseModel):
    pass


class ListingPublic(ListingBase):
    pass
