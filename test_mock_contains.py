#!/usr/bin/env python3
"""Test to verify the mock issue with CONNECTION_HANDLERS"""

from unittest.mock import Mock, patch
from modulink.types import ConnectionType


def test_mock_contains():
    """Test that shows the mock __contains__ issue"""
    print("Testing mock __contains__ behavior...")

    with patch("modulink.core.CONNECTION_HANDLERS") as mock_handlers:
        # Set up the mock like the test does
        mock_handler = Mock()
        mock_handlers.__getitem__.return_value = mock_handler

        # Test containment check
        http_enum = ConnectionType.HTTP
        print(f"Testing: {http_enum} in mock_handlers")

        try:
            result = http_enum in mock_handlers
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

        # Now set up __contains__ properly
        mock_handlers.__contains__.return_value = True

        print("After setting up __contains__:")
        result = http_enum in mock_handlers
        print(f"Result: {result}")


if __name__ == "__main__":
    test_mock_contains()
