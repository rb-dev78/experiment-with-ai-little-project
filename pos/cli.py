"""Interactive terminal UI for the Point of Sale system."""

from __future__ import annotations

import sys
from typing import Optional

from pos.models import Cart, TAX_RATE
from pos.pos import POSSystem
from pos.store import Store

# ANSI colour helpers (disabled automatically when not a TTY)
_USE_COLOUR = sys.stdout.isatty()

_RESET  = "\033[0m"  if _USE_COLOUR else ""
_BOLD   = "\033[1m"  if _USE_COLOUR else ""
_CYAN   = "\033[96m" if _USE_COLOUR else ""
_GREEN  = "\033[92m" if _USE_COLOUR else ""
_YELLOW = "\033[93m" if _USE_COLOUR else ""
_RED    = "\033[91m" if _USE_COLOUR else ""


def _header(text: str) -> None:
    print(f"\n{_BOLD}{_CYAN}{'=' * 42}{_RESET}")
    print(f"{_BOLD}{_CYAN}  {text}{_RESET}")
    print(f"{_BOLD}{_CYAN}{'=' * 42}{_RESET}")


def _info(text: str) -> None:
    print(f"{_GREEN}  ✔ {text}{_RESET}")


def _warn(text: str) -> None:
    print(f"{_YELLOW}  ⚠ {text}{_RESET}")


def _error(text: str) -> None:
    print(f"{_RED}  ✖ {text}{_RESET}")


def _prompt(text: str) -> str:
    return input(f"\n{_BOLD}{text}{_RESET} ").strip()


def _print_product_table(store: Store, in_stock_only: bool = False) -> None:
    products = store.list_products(in_stock_only=in_stock_only)
    if not products:
        _warn("No products available.")
        return
    print(f"\n  {'ID':>4}  {'Category':<14} {'Name':<22} {'Price':>7} {'Stock':>6}")
    print(f"  {'-'*4}  {'-'*14} {'-'*22} {'-'*7} {'-'*6}")
    for p in products:
        stock_str = str(p.stock) if p.stock > 0 else f"{_RED}0{_RESET}"
        print(
            f"  {p.id:>4}  {p.category:<14} {p.name:<22} "
            f"${p.price:>6.2f} {stock_str:>6}"
        )


def _print_cart(cart: Cart) -> None:
    if cart.is_empty():
        _warn("Cart is empty.")
        return
    print(f"\n  {'#':>3}  {'Name':<22} {'Qty':>4} {'Unit':>7} {'Sub':>8}")
    print(f"  {'-'*3}  {'-'*22} {'-'*4} {'-'*7} {'-'*8}")
    for i, item in enumerate(cart.items, 1):
        print(
            f"  {i:>3}  {item.product.name:<22} {item.quantity:>4} "
            f"${item.product.price:>6.2f} ${item.subtotal:>7.2f}"
        )
    print(f"\n  {'Subtotal':<34} ${cart.subtotal:>7.2f}")
    if cart.discount_percent:
        print(
            f"  {'Discount (' + str(cart.discount_percent) + '%)':<34} "
            f"-${cart.discount_amount:>6.2f}"
        )
    print(f"  {'Tax (' + str(TAX_RATE) + '%)':<34} ${cart.tax_amount:>7.2f}")
    print(f"  {_BOLD}{'TOTAL':<34} ${cart.total:>7.2f}{_RESET}")


def _ask_int(prompt: str, min_val: int = 1, max_val: Optional[int] = None) -> Optional[int]:
    raw = _prompt(prompt)
    try:
        value = int(raw)
        if value < min_val:
            _error(f"Value must be at least {min_val}.")
            return None
        if max_val is not None and value > max_val:
            _error(f"Value must be at most {max_val}.")
            return None
        return value
    except ValueError:
        _error("Please enter a valid integer.")
        return None


def _ask_float(prompt: str, min_val: float = 0.0) -> Optional[float]:
    raw = _prompt(prompt)
    try:
        value = float(raw)
        if value < min_val:
            _error(f"Value must be at least {min_val}.")
            return None
        return value
    except ValueError:
        _error("Please enter a valid number.")
        return None


# ------------------------------------------------------------------ #
# Action handlers                                                       #
# ------------------------------------------------------------------ #

def _action_view_products(pos: POSSystem) -> None:
    _header("PRODUCT CATALOG")
    _print_product_table(pos.store)


def _action_view_cart(pos: POSSystem) -> None:
    _header("CURRENT CART")
    _print_cart(pos.cart)


def _action_add_item(pos: POSSystem) -> None:
    _header("ADD ITEM TO CART")
    _print_product_table(pos.store, in_stock_only=True)
    product_id = _ask_int("Product ID:")
    if product_id is None:
        return
    quantity = _ask_int("Quantity:", min_val=1)
    if quantity is None:
        return
    try:
        pos.add_to_cart(product_id, quantity)
        _info(f"Added {quantity}× product #{product_id} to cart.")
    except Exception as exc:
        _error(str(exc))


def _action_remove_item(pos: POSSystem) -> None:
    _header("REMOVE ITEM FROM CART")
    _print_cart(pos.cart)
    if pos.cart.is_empty():
        return
    product_id = _ask_int("Product ID to remove (0 = cancel):", min_val=0)
    if not product_id:
        return
    raw_qty = _prompt("Quantity to remove (leave blank to remove all):")
    qty: Optional[int] = None
    if raw_qty:
        try:
            qty = int(raw_qty)
            if qty <= 0:
                _error("Quantity must be positive.")
                return
        except ValueError:
            _error("Invalid quantity.")
            return
    try:
        pos.remove_from_cart(product_id, qty)
        _info("Item removed from cart.")
    except Exception as exc:
        _error(str(exc))


def _action_apply_discount(pos: POSSystem) -> None:
    _header("APPLY DISCOUNT")
    percent = _ask_float("Discount percentage (0–100):", min_val=0.0)
    if percent is None:
        return
    if percent > 100:
        _error("Discount cannot exceed 100 %.")
        return
    try:
        pos.apply_discount(percent)
        _info(f"Discount of {percent}% applied.")
    except Exception as exc:
        _error(str(exc))


def _action_checkout(pos: POSSystem) -> None:
    _header("CHECKOUT")
    _print_cart(pos.cart)
    if pos.cart.is_empty():
        return
    payment = _ask_float(f"Payment amount (total = ${pos.cart.total:.2f}):", min_val=0.0)
    if payment is None:
        return
    try:
        receipt = pos.checkout(payment)
        print("\n" + receipt.render())
        _info("Transaction complete. Cart has been cleared.")
    except Exception as exc:
        _error(str(exc))


def _action_new_transaction(pos: POSSystem) -> None:
    if not pos.cart.is_empty():
        confirm = _prompt("Cart is not empty. Start new transaction? [y/N]:")
        if confirm.lower() != "y":
            _warn("Cancelled.")
            return
    pos.open_transaction()
    _info("New transaction started.")


def _action_last_receipt(pos: POSSystem) -> None:
    _header("LAST RECEIPT")
    if pos.last_receipt is None:
        _warn("No receipt available yet.")
    else:
        print("\n" + pos.last_receipt.render())


# ------------------------------------------------------------------ #
# Main menu loop                                                        #
# ------------------------------------------------------------------ #

_MENU = [
    ("1", "View product catalog",    _action_view_products),
    ("2", "Add item to cart",        _action_add_item),
    ("3", "Remove item from cart",   _action_remove_item),
    ("4", "View cart",               _action_view_cart),
    ("5", "Apply discount",          _action_apply_discount),
    ("6", "Checkout",                _action_checkout),
    ("7", "New transaction",         _action_new_transaction),
    ("8", "Print last receipt",      _action_last_receipt),
    ("0", "Exit",                    None),
]


def _print_menu() -> None:
    _header("PYTHON POINT OF SALE")
    for key, label, _ in _MENU:
        print(f"  {_BOLD}[{key}]{_RESET} {label}")


def run(store: Store) -> None:
    """Start the interactive POS terminal session."""
    pos = POSSystem(store)
    pos.open_transaction()

    print(f"\n{_BOLD}{_CYAN}  Welcome to Python POS!{_RESET}")
    print(f"  Tax rate: {TAX_RATE}%")

    while True:
        _print_menu()
        choice = _prompt("Select an option:")

        if choice == "0":
            print(f"\n{_BOLD}  Goodbye!{_RESET}\n")
            break

        action = next((fn for key, _, fn in _MENU if key == choice and fn), None)
        if action is None:
            _error(f"Invalid option '{choice}'. Please try again.")
        else:
            action(pos)
