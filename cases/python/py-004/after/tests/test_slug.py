from text.slug import slugify, unique_slug


def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("Crème brûlée") == "creme-brulee"
    assert slugify("!!!") == "untitled"


def test_unique_slug_appends_counter():
    assert unique_slug("Hello", set()) == "hello"
    assert unique_slug("Hello", {"hello"}) == "hello-2"
    assert unique_slug("Hello", {"hello", "hello-2"}) == "hello-3"
