"""Tests for checkout behavior."""

from __future__ import annotations

from autoresearch import core


def test_checkout_cart_creates_an_order_and_clears_the_cart() -> None:
    """The checkout helper should create an order total and empty the cart."""
    checkout_cart = getattr(core, "checkout_cart", None)

    assert callable(checkout_cart)

    if not callable(checkout_cart):
        return

    result = checkout_cart(
        [
            {"name": "Tea", "price_cents": 450, "quantity": 2},
            {"name": "Cake", "price_cents": 350, "quantity": 1},
        ]
    )

    assert result["order"]["total_cents"] == 1250
    assert result["cart"]["items"] == []
