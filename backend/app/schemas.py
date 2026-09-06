from pydantic import BaseModel


class AssetCreate(BaseModel):
    name: str
    category: str
    quantity: int
    condition: str
    location: str
    estimated_value: float | None = None
    status: str = "available"
    institution_id: int

class RequirementCreate(BaseModel):
    name: str
    category: str
    quantity: int
    condition: str
    location: str
    budget: float | None = None
    institution_id: int

class InstitutionCreate(BaseModel):
    name: str
    institution_type: str
    location: str
    contact_details: str | None = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    institution_id: int

class UserLogin(BaseModel):
    username: str
    password: str

class AssetStatusUpdate(BaseModel):
    status: str

class AllocationCreate(BaseModel):
    requirement_id: int
    asset_id: int
    quantity: int
    estimated_delivery_time: str | None = None