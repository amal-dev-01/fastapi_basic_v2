from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import Base, engine, get_db
from app.schemas import UserCreate, UserOut, Token, ItemOut, ItemCreate
from app.crud import get_user_by_username, create_user, create_item, delete_item, get_items, get_item, update_item
from app.security import verify_password
from app.auth import create_access_token, get_current_user, require_admin

# app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles
# uvicorn app.main:app --reload
# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


import os

app = FastAPI()

UPLOAD_DIR = "uploads"

# Ensure directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.requests import Request

origins = [
    "*"
]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     print(f"New request: {request.method} {request.url}")
#     response = await call_next(request)
#     return response



# @app.middleware("http")
# async def add_custom_header(request: Request, call_next):
#     response = await call_next(request)
#     response.headers["X-API-Version"] = "1.0.0" 
#     print(response.headers)
#     return response




# import time

# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start = time.time()
#     response = await call_next(request)
#     process_time = time.time() - start
#     response.headers["X-Process-Time"] = str(process_time)
#     return response

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limit Settings
RATE_LIMIT = {}
MAX_REQUESTS = 10
WINDOW = 60  # seconds

@app.middleware("http")
async def full_middleware(request: Request, call_next):
    start = time.time()

    ip = request.client.host
    now = time.time()

    # Rate limit
    RATE_LIMIT.setdefault(ip, [])
    RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < WINDOW]

    if len(RATE_LIMIT[ip]) >= MAX_REQUESTS:
        return JSONResponse(429, {"message": "Too many requests"})

    RATE_LIMIT[ip].append(now)

    # Next
    response = await call_next(request)

    # Custom headers
    response.headers["X-API-Version"] = "1.0.0"
    response.headers["X-Process-Time"] = str(time.time() - start)

    return response




@app.get("/")
def home():
    return f"hello"

@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(400, "Username already taken")

    return create_user(db, user)


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):

    user = get_user_by_username(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(400, "Invalid username or password")

    token = create_access_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/me", response_model=UserOut)
def read_me(current_user = Depends(get_current_user)):
    return current_user



@app.get("/dashboard")
def dashboard(current_user = Depends(get_current_user)):
    return {
        "message": "Dashboard Data",
        "username": current_user.username
    }


@app.get("/admin")
def admin_page(admin = Depends(require_admin)):
    return {"message": "Hello Admin!"}


@app.post("/items/", response_model=ItemOut)
def create_item_api(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return create_item(db, item, current_user.id)

@app.get("/items/", response_model=list[ItemOut])
def list_items(db: Session = Depends(get_db)):
    return get_items(db)


@app.put("/items/{item_id}", response_model=ItemOut)
def update_item_api(
    item_id: int,
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    updated = update_item(db, item_id, item, current_user.id)

    if updated is None:
        raise HTTPException(404, "Item not found")

    if updated == "not_allowed":
        raise HTTPException(403, "You cannot edit this item")

    return updated


@app.delete("/items/{item_id}")
def delete_item_api(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(403, "Admins only")

    success = delete_item(db, item_id)
    if not success:
        raise HTTPException(404, "Item not found")

    return {"message": "Item deleted"}




from fastapi import File, UploadFile
from app.crud import save_file_record
from app.schemas import FileOut

@app.post("/upload", response_model=FileOut)
async def upload_file(
    uploaded_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Save file to disk
    file_location = f"uploads/{uploaded_file.filename}"

    with open(file_location, "wb") as f:
        f.write(await uploaded_file.read())

    # Save database record
    file_record = save_file_record(
        db,
        filename=uploaded_file.filename,
        original=uploaded_file.filename,
        ftype=uploaded_file.content_type,
        user_id=current_user.id
    )

    return file_record


@app.post("/upload/multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    saved_files = []

    for file in files:
        file_location = f"uploads/{file.filename}"

        with open(file_location, "wb") as f:
            f.write(await file.read())

        saved = save_file_record(
            db,
            filename=file.filename,
            original=file.filename,
            ftype=file.content_type,
            user_id=current_user.id
        )
        saved_files.append(saved)

    return saved_files

@app.get("/my-files", response_model=list[FileOut])
def get_my_files(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(File).filter(File.owner_id == current_user.id).all()



import os

@app.delete("/file/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(404, "File not found")

    if file.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "Not allowed")

    file_path = f"uploads/{file.filename}"

    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(file)
    db.commit()

    return {"message": "File deleted successfully"}


@app.put("/file/{file_id}", response_model=FileOut)
async def update_file(
    file_id: int,
    new_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(404, "File not found")

    if file.owner_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    # 1. Delete old file
    old_path = f"uploads/{file.filename}"
    if os.path.exists(old_path):
        os.remove(old_path)

    # 2. Validate & save new file
    new_name = new_file.filename
    new_path = f"uploads/{new_name}"

    content = await new_file.read()
    with open(new_path, "wb") as f:
        f.write(content)

    # 3. Update DB
    file.filename = new_name
    file.original_name = new_file.filename
    db.commit()
    db.refresh(file)

    return file






from fastapi import Query
from app.crud import list_items_advanced

@app.get("/items/advanced")
def items_advanced(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),

    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    owner_id: int | None = None
    ):
    items, total = list_items_advanced(
        db=db,
        page=page,
        limit=limit,
        search=search,
        owner_id=owner_id
    )

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total // limit) + 1,
        "items": items
    }



from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "error": str(exc)
        }
    )


from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc: RequestValidationError):
    errors = [err['msg'] for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation Failed",
            "errors": errors
        }
    )

from app.logger import logger

@app.exception_handler(Exception)
def global_handler(request, exc):
    logger.error(f"Error: {exc} at {request.url}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

from sqlalchemy.exc import SQLAlchemyError

@app.exception_handler(SQLAlchemyError)
def db_exception_handler(request, exc):
    logger.error(f"DB Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Database error occurred"}
    )
