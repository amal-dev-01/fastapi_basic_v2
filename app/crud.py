from sqlalchemy.orm import Session
from app.models import User, Item, File
from app.schemas import UserCreate, ItemCreate
from app.security import hash_password

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed,
        role = user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user




def create_item(db: Session, item: ItemCreate, user_id: int):
    db_item = Item(
        title=item.title,
        description=item.description,
        owner_id=user_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session):
    return db.query(Item).all()

def get_item(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()

def update_item(db: Session, item_id: int, data: ItemCreate, user_id: int):
    db_item = get_item(db, item_id)
    if not db_item:
        return None
    if db_item.owner_id != user_id:
        return "not_allowed"

    db_item.title = data.title
    db_item.description = data.description

    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    db_item = get_item(db, item_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True



def save_file_record(db: Session, filename: str, original: str, ftype: str, user_id: int):
    db_file = File(
        filename=filename,
        original_name=original,
        file_type=ftype,
        owner_id=user_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Item

def list_items_advanced(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    owner_id: int | None = None
    ):
    query = db.query(Item)

    # Filtering by owner
    if owner_id:
        query = query.filter(Item.owner_id == owner_id)

    # Search
    if search:
        query = query.filter(
            or_(
                Item.title.ilike(f"%{search}%"),
                Item.description.ilike(f"%{search}%")
            )
        )

    # Count total records
    total = query.count()

    # Pagination
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()

    return results, total
