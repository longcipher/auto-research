"""Core utilities and shared logic."""

from __future__ import annotations

from typing import TypedDict


def greeting(name: str) -> str:
    """Build a greeting string.

    Args:
        name: The name to greet.

    Returns:
        A greeting message.

    """
    return f"Hello, {name}!"


class CartItem(TypedDict):
    """A line item in the shopping cart."""

    name: str
    price_cents: int
    quantity: int


class Cart(TypedDict):
    """A shopping cart."""

    items: list[CartItem]


class Order(TypedDict):
    """The order created by checkout."""

    items: list[CartItem]
    total_cents: int


class CheckoutResult(TypedDict):
    """The checkout result."""

    order: Order
    cart: Cart


def checkout_cart(items: list[CartItem]) -> CheckoutResult:
    """Create an order and clear the cart."""
    order_items = [item.copy() for item in items]
    total_cents = sum(item["price_cents"] * item["quantity"] for item in order_items)

    return {
        "order": {
            "items": order_items,
            "total_cents": total_cents,
        },
        "cart": {
            "items": [],
        },
    }
