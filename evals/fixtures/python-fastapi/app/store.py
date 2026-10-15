from app.models import Customer


class CustomerStore:
    """In-memory store; replaced by a database in production deployments."""

    def __init__(self) -> None:
        self._customers: dict[int, Customer] = {}

    def all(self) -> list[Customer]:
        return list(self._customers.values())

    def get(self, customer_id: int) -> Customer | None:
        return self._customers.get(customer_id)

    def add(self, customer: Customer) -> Customer:
        self._customers[customer.id] = customer
        return customer
