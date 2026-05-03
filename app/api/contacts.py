from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import ContactCreate, ContactUpdate, ContactResponse
from app.auth.deps import require_verified_user
from app.models import User

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_in: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    existing = crud.get_contact_by_email(db, current_user.id, str(contact_in.email))
    if existing:
        raise HTTPException(status_code=400, detail="Contact with this email already exists")
    return crud.create_contact(db, current_user.id, contact_in)


@router.get("", response_model=list[ContactResponse])
def list_contacts(
    skip: int = 0,
    limit: int = 100,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    return crud.get_contacts(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )


@router.get("/birthdays", response_model=list[ContactResponse])
def upcoming_birthdays(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    if days < 1 or days > 30:
        raise HTTPException(status_code=400, detail="days must be between 1 and 30")
    return crud.get_upcoming_birthdays(db, user_id=current_user.id, days=days)


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    contact = crud.get_contact_by_id(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    contact_in: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    contact = crud.get_contact_by_id(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact_in.email and str(contact_in.email) != contact.email:
        existing = crud.get_contact_by_email(db, current_user.id, str(contact_in.email))
        if existing:
            raise HTTPException(status_code=400, detail="Contact with this email already exists")

    return crud.update_contact(db, contact, contact_in)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    contact = crud.get_contact_by_id(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    crud.delete_contact(db, contact)
    return None