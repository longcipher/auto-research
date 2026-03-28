"""Property tests for checkout behavior."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from autoresearch.core import CartItem, checkout_cart

cart_items = st.fixed_dictionaries(
    {
        "name": st.text(min_size=1, max_size=32),
        "price_cents": st.integers(min_value=0, max_value=10_000),
        "quantity": st.integers(min_value=0, max_value=100),
    }
)


@given(st.lists(cart_items, max_size=20))
def test_checkout_cart_preserves_items_and_computes_total(items: list[CartItem]) -> None:
    """Checkout should preserve the order items, total, and empty the cart."""
    result = checkout_cart(items)

    assert result["order"]["items"] == items
    assert result["order"]["total_cents"] == sum(item["price_cents"] * item["quantity"] for item in items)
    assert result["cart"]["items"] == []
