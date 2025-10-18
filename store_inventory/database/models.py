from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: Optional[int]
    username: str
    password_hash: str
    role: str


@dataclass
class Supplier:
    supplier_id: Optional[int]
    name: str
    contact: str
    address: str


@dataclass
class Product:
    product_id: Optional[int]
    name: str
    category: str
    quantity: int
    price: float
    supplier_id: Optional[int]


@dataclass
class Sale:
    sale_id: Optional[int]
    product_id: int
    quantity_sold: int
    sale_date: str
    total_amount: float
