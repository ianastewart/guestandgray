import pytest
from table_manager.buttons import Button
from table_manager.session import update_url


def test_default_button():
    button = Button("Test button")
    html = button.render()
    assert "<button" in html
    assert 'type="button"' in html
    assert 'class="btn btn-primary"' in html
    assert 'name="test-button"' in html
    assert ">Test button</button" in html


def test_button_renders_attributes():
    button = Button(
        "Test button", css="btn btn-secondary", type="submit", name="test_name", hx_get="/test", hx_target="#target"
    )
    html = button.render()
    assert 'class="btn btn-secondary"' in html
    assert 'type="submit"' in html
    assert 'name="test_name"' in html
    assert 'hx-get="/test"' in html
    assert 'hx-target="#target"' in html


def test_link_button_when_href_present():
    button = Button("Test button", href="url")
    html = button.render()
    assert "<a" in html
    assert 'href="url"' in html
    assert "type" not in html


def test_update_url_empty():
    url = "http://test.com/"
    result = update_url(url, 25)
    assert result == "http://test.com/?per_page=25"


def test_update_url_existing_empty():
    url = "http://test.com/?per_page="
    result = update_url(url, 25)
    assert result == "http://test.com/?per_page=25"


def test_update_url_existing_empty_middle():
    url = "http://test.com/?x=1&per_page=&y=2"
    result = update_url(url, 25)
    assert result == "http://test.com/?x=1&per_page=25&y=2"


def test_update_url_existing_empty_end():
    url = "http://test.com/?x=1&per_page="
    result = update_url(url, 25)
    assert result == "http://test.com/?x=1&per_page=25"


def test_update_url_existing_sole():
    url = "http://test.com/?per_page=10"
    result = update_url(url, 25)
    assert result == "http://test.com/?per_page=25"


def test_update_url_existing_middle():
    url = "http://test.com/?x=1&per_page=10&y=2"
    result = update_url(url, 25)
    assert result == "http://test.com/?x=1&per_page=25&y=2"
