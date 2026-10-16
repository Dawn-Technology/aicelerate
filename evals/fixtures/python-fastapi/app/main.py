from fastapi import FastAPI, HTTPException

from app.models import Customer
from app.store import CustomerStore

app = FastAPI(title="customers-api")
store = CustomerStore()


@app.get("/customers")
def list_customers() -> list[Customer]:
    return store.all()


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int) -> Customer:
    customer = store.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return customer


@app.post("/customers", status_code=201)
def create_customer(customer: Customer) -> Customer:
    return store.add(customer)
