"""Unit tests for the Python POS system."""

import pytest

from pos.models import Cart, CartItem, Product, Receipt, TAX_RATE
from pos.pos import POSSystem
from pos.store import ProductNotFoundError, Store, create_demo_store


# ------------------------------------------------------------------ #
# Fixtures                                                              #
# ------------------------------------------------------------------ #

@pytest.fixture
def store() -> Store:
    s = Store()
    s.add_product("Apple",  0.50, "Fruit",  100)
    s.add_product("Banana", 0.30, "Fruit",   50)
    s.add_product("Laptop", 999.99, "Tech",   5)
    return s


@pytest.fixture
def pos(store: Store) -> POSSystem:
    p = POSSystem(store)
    p.open_transaction()
    return p


# ------------------------------------------------------------------ #
# Product model                                                         #
# ------------------------------------------------------------------ #

class TestProduct:
    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            Product(id=1, name="Bad", price=-1, category="X")

    def test_negative_stock_raises(self):
        with pytest.raises(ValueError):
            Product(id=1, name="Bad", price=1.0, category="X", stock=-1)

    def test_is_available(self):
        p = Product(id=1, name="A", price=1.0, category="X", stock=5)
        assert p.is_available(1)
        assert p.is_available(5)
        assert not p.is_available(6)

    def test_formatted_price(self):
        p = Product(id=1, name="A", price=1.5, category="X")
        assert p.formatted_price() == "$1.50"


# ------------------------------------------------------------------ #
# Cart model                                                            #
# ------------------------------------------------------------------ #

class TestCart:
    def _make_product(self, price: float = 10.0, stock: int = 20) -> Product:
        return Product(id=1, name="Test", price=price, category="Cat", stock=stock)

    def test_add_and_subtotal(self):
        cart = Cart()
        p = self._make_product(10.0)
        cart.add(p, 3)
        assert cart.subtotal == 30.0

    def test_add_existing_item_accumulates(self):
        cart = Cart()
        p = self._make_product(10.0, stock=10)
        cart.add(p, 2)
        cart.add(p, 3)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5

    def test_add_exceeds_stock_raises(self):
        cart = Cart()
        p = self._make_product(10.0, stock=2)
        with pytest.raises(ValueError, match="Insufficient stock"):
            cart.add(p, 3)

    def test_remove_all(self):
        cart = Cart()
        p = self._make_product()
        cart.add(p, 3)
        cart.remove(p.id)
        assert cart.is_empty()

    def test_remove_partial(self):
        cart = Cart()
        p = self._make_product()
        cart.add(p, 5)
        cart.remove(p.id, 2)
        assert cart.items[0].quantity == 3

    def test_remove_nonexistent_raises(self):
        cart = Cart()
        with pytest.raises(ValueError):
            cart.remove(999)

    def test_discount(self):
        cart = Cart()
        p = self._make_product(100.0)
        cart.add(p, 1)
        cart.apply_discount(10)
        assert cart.discount_amount == 10.0
        assert cart.total_before_tax == 90.0

    def test_invalid_discount_raises(self):
        cart = Cart()
        with pytest.raises(ValueError):
            cart.apply_discount(101)
        with pytest.raises(ValueError):
            cart.apply_discount(-5)

    def test_tax_calculation(self):
        cart = Cart()
        p = self._make_product(100.0)
        cart.add(p, 1)
        expected_tax = round(100.0 * TAX_RATE / 100, 2)
        assert cart.tax_amount == expected_tax
        assert cart.total == round(100.0 + expected_tax, 2)

    def test_clear(self):
        cart = Cart()
        p = self._make_product()
        cart.add(p, 2)
        cart.apply_discount(5)
        cart.clear()
        assert cart.is_empty()
        assert cart.discount_percent == 0.0


# ------------------------------------------------------------------ #
# Store                                                                 #
# ------------------------------------------------------------------ #

class TestStore:
    def test_add_and_get_product(self, store: Store):
        p = store.get_product(1)
        assert p.name == "Apple"

    def test_get_nonexistent_raises(self, store: Store):
        with pytest.raises(ProductNotFoundError):
            store.get_product(999)

    def test_list_products(self, store: Store):
        products = store.list_products()
        assert len(products) == 3

    def test_list_by_category(self, store: Store):
        fruits = store.list_products(category="Fruit")
        assert len(fruits) == 2

    def test_list_in_stock_only(self, store: Store):
        # Zero out one product's stock
        store.get_product(1).stock = 0
        in_stock = store.list_products(in_stock_only=True)
        assert all(p.stock > 0 for p in in_stock)

    def test_restock(self, store: Store):
        store.restock(1, 10)
        assert store.get_product(1).stock == 110

    def test_reduce_stock(self, store: Store):
        store.reduce_stock(1, 5)
        assert store.get_product(1).stock == 95

    def test_reduce_stock_below_zero_raises(self, store: Store):
        with pytest.raises(ValueError):
            store.reduce_stock(1, 9999)

    def test_categories(self, store: Store):
        cats = store.categories()
        assert "Fruit" in cats
        assert "Tech" in cats

    def test_create_demo_store(self):
        demo = create_demo_store()
        assert len(demo.list_products()) > 0


# ------------------------------------------------------------------ #
# POSSystem                                                             #
# ------------------------------------------------------------------ #

class TestPOSSystem:
    def test_add_to_cart(self, pos: POSSystem, store: Store):
        pos.add_to_cart(1, 2)
        assert pos.cart.item_count == 2

    def test_remove_from_cart(self, pos: POSSystem):
        pos.add_to_cart(1, 3)
        pos.remove_from_cart(1, 1)
        assert pos.cart.items[0].quantity == 2

    def test_apply_discount(self, pos: POSSystem):
        pos.add_to_cart(1, 2)
        pos.apply_discount(10)
        assert pos.cart.discount_percent == 10

    def test_checkout_success(self, pos: POSSystem, store: Store):
        pos.add_to_cart(1, 2)   # Apple × 2 = $1.00
        receipt = pos.checkout(payment=10.00)
        assert receipt.total > 0
        assert receipt.change == round(10.00 - receipt.total, 2)
        # Stock should be deducted
        assert store.get_product(1).stock == 98

    def test_checkout_empty_cart_raises(self, pos: POSSystem):
        with pytest.raises(ValueError, match="empty"):
            pos.checkout(payment=10.00)

    def test_checkout_insufficient_payment_raises(self, pos: POSSystem):
        pos.add_to_cart(3, 1)   # Laptop $999.99
        with pytest.raises(ValueError, match="Insufficient payment"):
            pos.checkout(payment=1.00)

    def test_cart_cleared_after_checkout(self, pos: POSSystem):
        pos.add_to_cart(1, 1)
        pos.checkout(payment=5.00)
        assert pos.cart.is_empty()

    def test_transaction_counter_increments(self, pos: POSSystem):
        pos.add_to_cart(1, 1)
        pos.checkout(payment=5.00)
        pos.open_transaction()
        pos.add_to_cart(2, 1)
        pos.checkout(payment=5.00)
        assert pos.transaction_count() == 2

    def test_last_receipt(self, pos: POSSystem):
        assert pos.last_receipt is None
        pos.add_to_cart(1, 1)
        pos.checkout(payment=5.00)
        assert pos.last_receipt is not None

    def test_new_transaction_clears_cart(self, pos: POSSystem):
        pos.add_to_cart(1, 2)
        pos.open_transaction()
        assert pos.cart.is_empty()


# ------------------------------------------------------------------ #
# Receipt rendering                                                     #
# ------------------------------------------------------------------ #

class TestReceipt:
    def test_render_contains_key_fields(self, pos: POSSystem):
        pos.add_to_cart(1, 2)
        pos.apply_discount(5)
        receipt = pos.checkout(payment=10.00)
        rendered = receipt.render()
        assert "Apple" in rendered
        assert "TOTAL" in rendered
        assert "Discount" in rendered
        assert "Thank you" in rendered

    def test_receipt_totals_are_consistent(self, pos: POSSystem):
        pos.add_to_cart(1, 4)  # Apple × 4 = $2.00 subtotal
        receipt = pos.checkout(payment=5.00)
        assert receipt.subtotal == 2.00
        assert receipt.discount_amount == 0.0
        expected_tax = round(2.00 * TAX_RATE / 100, 2)
        assert receipt.tax_amount == expected_tax
        assert receipt.total == round(2.00 + expected_tax, 2)
        assert receipt.change == round(5.00 - receipt.total, 2)
