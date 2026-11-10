from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, Base
from models import Contact, Product, Production, Invoice, InvoiceItem, Transaction, InvoiceStatus
import schemas

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Unified Data & POS Sync Engine")


# ---------------- CONTACTS ----------------
@app.post("/contacts/", response_model=schemas.ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.get("/contacts/", response_model=List[schemas.ContactResponse])
def get_contacts(db: Session = Depends(get_db)):
    return db.query(Contact).all()


# ---------------- PRODUCTS & PRODUCTION ----------------
@app.post("/products/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.post("/production/log/")
def log_production(log: schemas.ProductionLog, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == log.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Increment stock
    product.stock_quantity += log.quantity_produced

    # Record production run
    db_production = Production(**log.model_dump())
    db.add(db_production)
    db.commit()

    return {
        "message": f"Successfully added {log.quantity_produced} units to {product.name}",
        "new_stock_level": product.stock_quantity
    }


# ---------------- INVOICES ----------------
@app.post("/invoices/", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice_data: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    # Validate contact
    contact = db.query(Contact).filter(Contact.id == invoice_data.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    total_amount = 0.0
    items_to_create = []

    # Validate stock and calculate total
    for item in invoice_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")

        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {product.name}. Requested: {item.quantity}, Available: {product.stock_quantity}"
            )

        subtotal = product.unit_price * item.quantity
        total_amount += subtotal

        # Auto-decrement product stock level upon invoice generation
        product.stock_quantity -= item.quantity

        items_to_create.append(
            InvoiceItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.unit_price,
                subtotal=subtotal
            )
        )

    # Save Invoice
    db_invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        contact_id=invoice_data.contact_id,
        status=InvoiceStatus.UNPAID,
        total_amount=total_amount,
        items=items_to_create
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


# ---------------- POS TERMINAL SYNC WEBHOOK ----------------
@app.post("/webhooks/pos-sync/")
def pos_payment_webhook(payload: schemas.POSWebhookPayload, db: Session = Depends(get_db)):
    """
    Endpoint targeted by POS machines or payment gateway webhooks.
    Automatically updates invoice to 'PAID' and logs the transaction.
    """
    # Fetch invoice
    invoice = db.query(Invoice).filter(Invoice.invoice_number == payload.invoice_number).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice matching POS reference not found")

    if invoice.status == InvoiceStatus.PAID:
        return {"message": "Invoice already marked as paid"}

    # Update Invoice Status
    invoice.status = InvoiceStatus.PAID

    # Log Transaction linked to Contact, Invoice, and Terminal ID
    transaction = Transaction(
        contact_id=invoice.contact_id,
        invoice_id=invoice.id,
        terminal_id=payload.terminal_id,
        payment_ref=payload.payment_ref,
        amount=payload.amount_paid,
        payment_method=payload.payment_method
    )
    db.add(transaction)
    db.commit()

    return {
        "status": "Success",
        "invoice_number": invoice.invoice_number,
        "payment_status": "PAID",
        "terminal": payload.terminal_id,
        "amount_processed": payload.amount_paid
    }