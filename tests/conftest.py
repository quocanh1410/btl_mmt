import pytest


def pytest_collection_modifyitems(items):
    """Test gắn @pytest.mark.todo được coi là xfail (không làm đỏ CI).
    Khi hiện thực xong, BỎ marker todo để test trở thành bắt buộc."""
    for item in items:
        if item.get_closest_marker("todo"):
            item.add_marker(pytest.mark.xfail(reason="chưa hiện thực", strict=False))
