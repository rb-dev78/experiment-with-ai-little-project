"""Product catalog — manages the available products and their stock."""

from __future__ import annotations

from typing import Dict, List, Optional

from pos.models import Product


class ProductNotFoundError(Exception):
    pass


class Store:
    """Maintains a catalog of products with stock management."""

    def __init__(self) -> None:
        self._products: Dict[int, Product] = {}
        self._next_id: int = 1

    # ------------------------------------------------------------------ #
    # Catalog management                                                    #
    # ------------------------------------------------------------------ #

    def add_product(
        self,
        name: str,
        price: float,
        category: str,
        stock: int = 0,
    ) -> Product:
        """Create and register a new product; return the Product object."""
        product = Product(
            id=self._next_id,
            name=name,
            price=price,
            category=category,
            stock=stock,
        )
        self._products[self._next_id] = product
        self._next_id += 1
        return product

    def get_product(self, product_id: int) -> Product:
        """Return the product with *product_id* or raise ProductNotFoundError."""
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFoundError(f"No product with id {product_id}")
        return product

    def list_products(
        self,
        category: Optional[str] = None,
        in_stock_only: bool = False,
    ) -> List[Product]:
        """Return a filtered, sorted list of products."""
        products = list(self._products.values())
        if category:
            products = [p for p in products if p.category.lower() == category.lower()]
        if in_stock_only:
            products = [p for p in products if p.stock > 0]
        return sorted(products, key=lambda p: (p.category, p.name))

    def categories(self) -> List[str]:
        """Return a sorted list of unique category names."""
        return sorted({p.category for p in self._products.values()})

    # ------------------------------------------------------------------ #
    # Stock management                                                      #
    # ------------------------------------------------------------------ #

    def restock(self, product_id: int, quantity: int) -> None:
        """Add *quantity* units to a product's stock."""
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")
        product = self.get_product(product_id)
        product.stock += quantity

    def reduce_stock(self, product_id: int, quantity: int) -> None:
        """Remove *quantity* units from a product's stock after a sale."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        product = self.get_product(product_id)
        if product.stock < quantity:
            raise ValueError(
                f"Cannot reduce stock of '{product.name}' by {quantity}: "
                f"only {product.stock} in stock"
            )
        product.stock -= quantity


def create_demo_store() -> Store:
    """Return a pre-populated store with sample products."""
    store = Store()

    # Beverages
    store.add_product("Coffee",        2.50,  "Beverages",  50)
    store.add_product("Tea",           1.75,  "Beverages",  60)
    store.add_product("Orange Juice",  3.00,  "Beverages",  30)
    store.add_product("Mineral Water", 1.00,  "Beverages", 100)

    # Food
    store.add_product("Croissant",     2.25,  "Food",       40)
    store.add_product("Sandwich",      5.50,  "Food",       25)
    store.add_product("Muffin",        2.00,  "Food",       35)
    store.add_product("Salad",         7.00,  "Food",       15)

    # Electronics
    store.add_product("USB Cable",     9.99,  "Electronics", 20)
    store.add_product("Phone Stand",  14.99,  "Electronics", 12)
    store.add_product("Earbuds",      29.99,  "Electronics",  8)

    # Stationery
    store.add_product("Notebook",      3.99,  "Stationery",  30)
    store.add_product("Pen Set",       5.49,  "Stationery",  45)
    store.add_product("Sticky Notes",  2.49,  "Stationery",  50)

    return store
