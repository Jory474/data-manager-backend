import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class ContactType(str, enum.Enum):
    CUSTOMER = "customer"
    CLIENT = "client"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    UNPAID = "unpaid"
    PAID = "paid"
    CANCELLED = "cancelled"


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    contact_type = Column(Enum(ContactType), default=ContactType.CUSTOMER)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="contact")
    transactions = relationship("Transaction", back_populates="contact")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)

    productions = relationship("Production", back_populates="product")
    invoice_items = relationship("InvoiceItem", back_populates="product")


class Production(Base):
    __tablename__ = "productions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_produced = Column(Integer, nullable=False)
    batch_number = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="productions")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.UNPAID)
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice")
    transactions = relationship("Transaction", back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", back_populates="invoice_items")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    terminal_id = Column(String, nullable=True)  # POS Device Identifier
    payment_ref = Column(String, unique=True, index=True, nullable=True)  # Gateway Transaction Hash/RRN
    amount = Column(Float, nullable=False)
    payment_method = Column(String, default="POS")
    timestamp = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="transactions")
    invoice = relationship("Invoice", back_populates="transactions")