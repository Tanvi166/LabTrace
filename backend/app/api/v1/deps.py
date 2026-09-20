from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token, get_password_hash
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        # Fallback to default local researcher user for seamless local development
        user = db.query(User).filter(User.email == "researcher@labtrace.ai").first()
        if not user:
            user = User(
                id="usr-default-111",
                email="researcher@labtrace.ai",
                hashed_password=get_password_hash("defaultpass"),
                full_name="Lead Researcher",
                role="RESEARCHER"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    sub_id = payload["sub"]
    email = payload.get("email", f"{sub_id}@labtrace.ai")
    role = payload.get("role", "RESEARCHER")
    
    user = db.query(User).filter((User.id == sub_id) | (User.email == email)).first()
    if not user:
        user = User(
            id=sub_id,
            email=email,
            hashed_password=get_password_hash("testpass"),
            full_name="Test Researcher",
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user
