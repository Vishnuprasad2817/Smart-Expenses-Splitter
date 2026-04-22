from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class GroupResponse(GroupBase):
    id: int
    created_at: str
    members: List[UserResponse] = []

class ExpenseSplitCreate(BaseModel):
    user_id: int
    amount_owed: float

class ExpenseCreate(BaseModel):
    group_id: int
    description: str
    amount: float
    paid_by: int
    splits: List[ExpenseSplitCreate]

class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    description: str
    amount: float
    paid_by: int
    category: Optional[str]
    date: str
    splits: List[dict] = []

class AddMemberRequest(BaseModel):
    user_id: int
