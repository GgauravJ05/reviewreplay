from shop.cart import Cart
from shop.checkout import shipping_cents, total_cents


def test_empty_cart_has_no_shipping():
    assert shipping_cents(Cart()) == 0


def test_large_order_ships_free():
    cart = Cart()
    cart.add("desk", 12_000)
    assert shipping_cents(cart) == 0
    assert total_cents(cart) == 12_000
