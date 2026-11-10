from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import ContactType, InvoiceStatus


# Contact Schemas
class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_type: ContactType


class ContactResponse(ContactCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# Product Schemas
class ProductCreate(BaseModel):
    sku: str
    name: str
    unit_price: float
    stock_quantity: int = 0


class ProductResponse(ProductCreate):
    id: int
    class Config:
        from_attributes = True


# Production Schemas
class ProductionLog(BaseModel):
    product_id: int
    quantity_produced: int
    batch_number: Optional[str] = None


# Invoice Schemas
class InvoiceItemCreate(BaseModel):
    product_id: int
    quantity: int


class InvoiceCreate(BaseModel):
    invoice_number: str
    contact_id: int
    items: List[InvoiceItemCreate]


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    contact_id: int
    status: InvoiceStatus
    total_amount: float
    created_at: datetime
    class Config:
        from_attributes = True


# POS Sync Webhook Schema
class POSWebhookPayload(BaseModel):
    terminal_id: str
    payment_ref: str
    invoice_number: str
    amount_paid: float
    payment_method: str = "CARD_POS"