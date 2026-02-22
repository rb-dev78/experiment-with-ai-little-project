"""Core POS logic: ties together the store, cart, and receipt generation."""

from __future__ import annotations

from typing import Optional

from pos.models import Cart, Receipt, TAX_RATE
from pos.store import Store


class POSSystem:
    """
    The main Point-of-Sale controller.

    Usage::

        pos = POSSystem(store)
        pos.open_transaction()
        pos.add_to_cart(product_id=1, quantity=2)
        pos.apply_discount(10)          # 10 % off
        receipt = pos.checkout(payment=50.00)
        print(receipt.render())
    """

    def __init__(self, store: Store) -> None:
        self._store = store
        self._cart: Cart = Cart()
        self._transaction_counter: int = 0
        self._last_receipt: Optional[Receipt] = None

    # ------------------------------------------------------------------ #
    # Transaction lifecycle                                                 #
    # ------------------------------------------------------------------ #

    def open_transaction(self) -> None:
        """Start a new transaction by clearing the current cart."""
        self._cart.clear()

    # ------------------------------------------------------------------ #
    # Cart operations                                                       #
    # ------------------------------------------------------------------ #

    @property
    def cart(self) -> Cart:
        return self._cart

    def add_to_cart(self, product_id: int, quantity: int = 1) -> None:
        """Look up *product_id* in the store and add it to the cart."""
        product = self._store.get_product(product_id)
        self._cart.add(product, quantity)

    def remove_from_cart(self, product_id: int, quantity: Optional[int] = None) -> None:
        """Remove *quantity* units of *product_id* from the cart.

        If *quantity* is None the entire product line is removed.
        """
        self._cart.remove(product_id, quantity)

    def apply_discount(self, percent: float) -> None:
        """Apply a percentage discount to the current cart."""
        self._cart.apply_discount(percent)

    # ------------------------------------------------------------------ #
    # Checkout                                                              #
    # ------------------------------------------------------------------ #

    def checkout(self, payment: float) -> Receipt:
        """
        Finalise the transaction, deduct stock, and return a Receipt.

        Raises:
            ValueError: If the cart is empty or payment is insufficient.
        """
        if self._cart.is_empty():
            raise ValueError("Cannot checkout: the cart is empty.")
        if payment < self._cart.total:
            raise ValueError(
                f"Insufficient payment: total is ${self._cart.total:.2f}, "
                f"payment is ${payment:.2f}."
            )

        self._transaction_counter += 1

        # Deduct stock for every sold item
        for item in self._cart.items:
            self._store.reduce_stock(item.product.id, item.quantity)

        # Build receipt from a snapshot of the current cart
        receipt = Receipt(
            transaction_id=self._transaction_counter,
            cart_snapshot=list(self._cart.items),
            subtotal=self._cart.subtotal,
            discount_percent=self._cart.discount_percent,
            discount_amount=self._cart.discount_amount,
            tax_rate=TAX_RATE,
            tax_amount=self._cart.tax_amount,
            total=self._cart.total,
            payment=round(payment, 2),
            change=round(payment - self._cart.total, 2),
        )

        self._last_receipt = receipt
        self._cart.clear()
        return receipt

    # ------------------------------------------------------------------ #
    # Helpers                                                               #
    # ------------------------------------------------------------------ #

    @property
    def store(self) -> Store:
        return self._store

    @property
    def last_receipt(self) -> Optional[Receipt]:
        return self._last_receipt

    def transaction_count(self) -> int:
        return self._transaction_counter
