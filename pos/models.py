"""Data models for the Point of Sale system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Product:
    """A product available for sale."""

    id: int
    name: str
    price: float
    category: str
    stock: int = 0

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError(f"Price cannot be negative: {self.price}")
        if self.stock < 0:
            raise ValueError(f"Stock cannot be negative: {self.stock}")

    def is_available(self, quantity: int = 1) -> bool:
        """Return True if at least *quantity* units are in stock."""
        return self.stock >= quantity

    def formatted_price(self) -> str:
        return f"${self.price:.2f}"


@dataclass
class CartItem:
    """A product with a chosen quantity in the shopping cart."""

    product: Product
    quantity: int = 1

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be at least 1, got {self.quantity}")

    @property
    def subtotal(self) -> float:
        return round(self.product.price * self.quantity, 2)


@dataclass
class Cart:
    """A shopping cart holding cart items and an optional discount."""

    items: List[CartItem] = field(default_factory=list)
    discount_percent: float = 0.0  # 0-100

    # ------------------------------------------------------------------ #
    # Computed totals                                                       #
    # ------------------------------------------------------------------ #

    @property
    def subtotal(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    @property
    def discount_amount(self) -> float:
        return round(self.subtotal * self.discount_percent / 100, 2)

    @property
    def total_before_tax(self) -> float:
        return round(self.subtotal - self.discount_amount, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.total_before_tax * TAX_RATE / 100, 2)

    @property
    def total(self) -> float:
        return round(self.total_before_tax + self.tax_amount, 2)

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    # ------------------------------------------------------------------ #
    # Mutation helpers                                                      #
    # ------------------------------------------------------------------ #

    def find_item(self, product_id: int) -> Optional[CartItem]:
        for item in self.items:
            if item.product.id == product_id:
                return item
        return None

    def add(self, product: Product, quantity: int = 1) -> None:
        if not product.is_available(quantity):
            raise ValueError(
                f"Insufficient stock for '{product.name}' "
                f"(requested {quantity}, available {product.stock})"
            )
        existing = self.find_item(product.id)
        if existing:
            total_qty = existing.quantity + quantity
            if not product.is_available(total_qty):
                raise ValueError(
                    f"Insufficient stock for '{product.name}' "
                    f"(requested {total_qty} total, available {product.stock})"
                )
            existing.quantity = total_qty
        else:
            self.items.append(CartItem(product=product, quantity=quantity))

    def remove(self, product_id: int, quantity: Optional[int] = None) -> None:
        item = self.find_item(product_id)
        if item is None:
            raise ValueError(f"Product id {product_id} not found in cart")
        if quantity is None or quantity >= item.quantity:
            self.items.remove(item)
        else:
            item.quantity -= quantity

    def clear(self) -> None:
        self.items.clear()
        self.discount_percent = 0.0

    def apply_discount(self, percent: float) -> None:
        if not 0 <= percent <= 100:
            raise ValueError(f"Discount must be between 0 and 100, got {percent}")
        self.discount_percent = percent


# Tax rate applied after discounts (percentage, e.g. 8.5 means 8.5 %)
TAX_RATE: float = 8.5


@dataclass
class Receipt:
    """A finalised sale receipt."""

    transaction_id: int
    cart_snapshot: List[CartItem]
    subtotal: float
    discount_percent: float
    discount_amount: float
    tax_rate: float
    tax_amount: float
    total: float
    payment: float
    change: float
    timestamp: datetime = field(default_factory=datetime.now)

    def render(self) -> str:
        """Return a formatted receipt string."""
        line = "-" * 42
        header = "=" * 42
        lines = [
            header,
            "       PYTHON POINT OF SALE".center(42),
            header,
            f"  Transaction: #{self.transaction_id:06d}",
            f"  Date: {self.timestamp.strftime('%Y-%m-%d  %H:%M:%S')}",
            line,
            f"  {'ITEM':<22} {'QTY':>4} {'PRICE':>7} {'SUB':>7}",
            line,
        ]
        for item in self.cart_snapshot:
            lines.append(
                f"  {item.product.name:<22} {item.quantity:>4} "
                f"${item.product.price:>6.2f} ${item.subtotal:>6.2f}"
            )
        lines += [
            line,
            f"  {'Subtotal':<30} ${self.subtotal:>7.2f}",
        ]
        if self.discount_percent:
            lines.append(
                f"  {'Discount (' + str(self.discount_percent) + '%)':<30} -${self.discount_amount:>6.2f}"
            )
        lines += [
            f"  {'Tax (' + str(self.tax_rate) + '%)':<30} ${self.tax_amount:>7.2f}",
            f"  {'TOTAL':<30} ${self.total:>7.2f}",
            line,
            f"  {'Payment':<30} ${self.payment:>7.2f}",
            f"  {'Change':<30} ${self.change:>7.2f}",
            header,
            "        Thank you for shopping!".center(42),
            header,
        ]
        return "\n".join(lines)
