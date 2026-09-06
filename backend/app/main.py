from app.database import engine, Base
import jwt
from fastapi.security import HTTPBearer
from app.schemas import AssetCreate, AssetStatusUpdate, AllocationCreate, RequirementCreate, InstitutionCreate, UserCreate, UserLogin
from app.models import Asset, AuditLog, Requirement, Institution, User, Allocation
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from fastapi import Depends
from app import models
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text

from app.database import engine

app = FastAPI()
password_hash = PasswordHash.recommended()
JWT_SECRET = "change-this-later"
JWT_ALGORITHM = "HS256"
Base.metadata.create_all(bind=engine)
security = HTTPBearer()


def get_current_user(credentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return payload

@app.get("/")
def root():
    return {"message": "Public Sector Surplus Exchange API is running"}


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar()}

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

@app.post("/assets")
def create_asset(asset: AssetCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["institution_id"] != asset.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only create assets for your institution"
            )
    institution = db.query(Institution).filter(
        Institution.id == asset.institution_id
    ).first()

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
            )
    new_asset = Asset(
    name=asset.name,
    category=asset.category,
    quantity=asset.quantity,
    condition=asset.condition,
    location=asset.location,
    estimated_value=asset.estimated_value,
    status=asset.status,
    institution_id=asset.institution_id
    )

    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    return new_asset

@app.get("/assets/{asset_id}")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return asset

@app.put("/assets/{asset_id}")
def update_asset(asset_id: int, asset: AssetCreate, db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    existing_asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not existing_asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
            )

    if current_user["institution_id"] != existing_asset.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update assets belonging to your institution"
            )

    institution = db.query(Institution).filter(
        Institution.id == asset.institution_id
    ).first()

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
            )

    existing_asset.name = asset.name
    existing_asset.category = asset.category
    existing_asset.quantity = asset.quantity
    existing_asset.condition = asset.condition
    existing_asset.location = asset.location
    existing_asset.estimated_value = asset.estimated_value
    existing_asset.status = asset.status
    existing_asset.institution_id = asset.institution_id

    db.commit()
    db.refresh(existing_asset)

    return existing_asset

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    existing_asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not existing_asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
            )
    if current_user["institution_id"] != existing_asset.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete assets belonging to your institution"
            )

    db.delete(existing_asset)
    db.commit()

    return {"message": "Asset deleted successfully"}

@app.post("/allocations")
def create_allocation(
    allocation: AllocationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    requirement = db.query(Requirement).filter(
        Requirement.id == allocation.requirement_id
    ).first()

    if not requirement:
        raise HTTPException(
            status_code=404,
            detail="Requirement not found"
        )

    asset = db.query(Asset).filter(
        Asset.id == allocation.asset_id
    ).first()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    if current_user["institution_id"] != requirement.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only allocate to requirements from your institution"
        )

    if asset.status != "available":
        raise HTTPException(
            status_code=400,
            detail="Asset is not available"
        )

    if allocation.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Allocation quantity must be greater than zero"
        )

    if allocation.quantity > asset.quantity:
        raise HTTPException(
            status_code=400,
            detail="Allocation quantity exceeds available asset quantity"
        )

    new_allocation = Allocation(
        requirement_id=allocation.requirement_id,
        asset_id=allocation.asset_id,
        quantity=allocation.quantity,
        status="recommended",
        estimated_delivery_time=allocation.estimated_delivery_time
        )

    db.add(new_allocation)
    db.commit()
    db.refresh(new_allocation)

    audit_log = AuditLog(
        user_id=current_user["user_id"],
        action="CREATE_ALLOCATION",
        asset_id=asset.id,
        allocation_id=new_allocation.id,
        details=f"Allocated {allocation.quantity} units"
    )

    db.add(audit_log)
    db.commit()

    return {
        "id": new_allocation.id,
        "requirement_id": new_allocation.requirement_id,
        "asset_id": new_allocation.asset_id,
        "quantity": new_allocation.quantity,
        "status": new_allocation.status,
        "estimated_delivery_time": new_allocation.estimated_delivery_time
        }

@app.patch("/allocations/{allocation_id}/approve")
def approve_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    allocation = db.query(Allocation).filter(
        Allocation.id == allocation_id
    ).first()

    if not allocation:
        raise HTTPException(
            status_code=404,
            detail="Allocation not found"
        )

    requirement = db.query(Requirement).filter(
        Requirement.id == allocation.requirement_id
    ).first()

    if current_user["institution_id"] != requirement.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only approve allocations for your institution"
        )

    if allocation.status != "recommended":
        raise HTTPException(
            status_code=400,
            detail="Only recommended allocations can be approved"
        )

    asset = db.query(Asset).filter(
        Asset.id == allocation.asset_id
    ).first()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    if allocation.quantity > asset.quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient asset quantity"
        )

    asset.quantity -= allocation.quantity
    allocation.status = "approved"

    db.commit()
    db.refresh(allocation)

    audit_log = AuditLog(
        user_id=current_user["user_id"],
        action="APPROVE_ALLOCATION",
        asset_id=asset.id,
        allocation_id=allocation.id,
        details=f"Approved allocation of {allocation.quantity} units"
    )

    db.add(audit_log)
    db.commit()

    return {
        "id": allocation.id,
        "requirement_id": allocation.requirement_id,
        "asset_id": allocation.asset_id,
        "quantity": allocation.quantity,
        "status": allocation.status
    }

@app.patch("/allocations/{allocation_id}/reject")
def reject_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    allocation = db.query(Allocation).filter(
        Allocation.id == allocation_id
    ).first()

    if not allocation:
        raise HTTPException(
            status_code=404,
            detail="Allocation not found"
        )

    requirement = db.query(Requirement).filter(
        Requirement.id == allocation.requirement_id
    ).first()

    if current_user["institution_id"] != requirement.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only reject allocations for your institution"
        )

    if allocation.status != "recommended":
        raise HTTPException(
            status_code=400,
            detail="Only recommended allocations can be rejected"
        )

    allocation.status = "rejected"

    db.commit()
    db.refresh(allocation)

    audit_log = AuditLog(
        user_id=current_user["user_id"],
        action="REJECT_ALLOCATION",
        asset_id=allocation.asset_id,
        allocation_id=allocation.id,
        details=f"Rejected allocation of {allocation.quantity} units"
    )

    db.add(audit_log)
    db.commit()

    return {
        "id": allocation.id,
        "requirement_id": allocation.requirement_id,
        "asset_id": allocation.asset_id,
        "quantity": allocation.quantity,
        "status": allocation.status
    }

@app.get("/allocations")
def get_allocations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    allocations = db.query(Allocation).join(
        Requirement,
        Allocation.requirement_id == Requirement.id
    ).filter(
        Requirement.institution_id == current_user["institution_id"]
    ).all()

    return [
        {
            "id": allocation.id,
            "requirement_id": allocation.requirement_id,
            "asset_id": allocation.asset_id,
            "quantity": allocation.quantity,
            "status": allocation.status
        }
        for allocation in allocations
    ]

@app.get("/matching/candidates/{requirement_id}")
def get_matching_candidates(
    requirement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id
    ).first()

    if not requirement:
        raise HTTPException(
            status_code=404,
            detail="Requirement not found"
        )

    if current_user["institution_id"] != requirement.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access matching data for your institution"
        )

    assets = db.query(Asset).filter(
        Asset.status == "available",
        Asset.quantity > 0
    ).all()

    return assets

@app.post("/requirements")
def create_requirement(
    requirement: RequirementCreate,
    db: Session = Depends(get_db)
):
    institution = db.query(Institution).filter(
        Institution.id == requirement.institution_id
    ).first()

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
            )
    new_requirement = Requirement(
        name=requirement.name,
        category=requirement.category,
        quantity=requirement.quantity,
        condition=requirement.condition,
        location=requirement.location,
        budget=requirement.budget,
        institution_id=requirement.institution_id
    )

    db.add(new_requirement)
    db.commit()
    db.refresh(new_requirement)

    return new_requirement

@app.get("/requirements")
def get_requirements(db: Session = Depends(get_db)):
    return db.query(Requirement).all()

@app.get("/requirements/{requirement_id}")
def get_requirement(
    requirement_id: int,
    db: Session = Depends(get_db)
):
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id
    ).first()

    if not requirement:
        raise HTTPException(
            status_code=404,
            detail="Requirement not found"
        )

    return requirement

@app.post("/institutions")
def create_institution(
    institution: InstitutionCreate,
    db: Session = Depends(get_db)
):
    new_institution = Institution(
        name=institution.name,
        institution_type=institution.institution_type,
        location=institution.location,
        contact_details=institution.contact_details
        )

    db.add(new_institution)
    db.commit()
    db.refresh(new_institution)

    return new_institution

@app.get("/institutions")
def get_institutions(db: Session = Depends(get_db)):
    return db.query(Institution).all()

@app.get("/assets")
def get_assets(db: Session = Depends(get_db)):
    return db.query(Asset).all()

@app.post("/users")
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    institution = db.query(Institution).filter(
        Institution.id == user.institution_id
    ).first()

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    existing_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    new_user = User(
        username=user.username,
        password_hash=password_hash.hash(user.password),
        role=user.role,
        institution_id=user.institution_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "role": new_user.role,
        "institution_id": new_user.institution_id
    }

@app.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not password_hash.verify(
        user.password,
        existing_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = jwt.encode(
        {
            "user_id": existing_user.id,
            "username": existing_user.username,
            "role": existing_user.role,
            "institution_id": existing_user.institution_id
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.patch("/assets/{asset_id}/status")
def update_asset_status(
    asset_id: int,
    status_update: AssetStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    existing_asset = db.query(Asset).filter(
        Asset.id == asset_id
    ).first()

    if not existing_asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    if current_user["institution_id"] != existing_asset.institution_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update assets belonging to your institution"
        )

    existing_asset.status = status_update.status

    db.commit()
    db.refresh(existing_asset)

    return existing_asset
