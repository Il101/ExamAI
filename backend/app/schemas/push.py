from pydantic import BaseModel, HttpUrl


class PushSubscriptionCreate(BaseModel):
    """Schema for creating a new push subscription"""
    endpoint: str
    p256dh: str
    auth: str


class PushSubscriptionResponse(BaseModel):
    """Schema for push subscription response"""
    endpoint: str
    
    class Config:
        from_attributes = True
