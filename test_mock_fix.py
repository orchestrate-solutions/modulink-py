#!/usr/bin/env python3

"""Quick test to verify the mock fix for CONNECTION_HANDLERS"""

from unittest.mock import patch, Mock
from modulink.types import ConnectionType


def test_mock_fix():
    """Test that the mock works correctly with __contains__"""
    print("Testing mock fix...")

    with patch("modulink.core.CONNECTION_HANDLERS") as mock_handlers:
        # Set up the mock to behave like a dictionary
        mock_handler = Mock()
        mock_handlers.__getitem__.return_value = mock_handler
        mock_handlers.__contains__.return_value = True  # This is the key fix

        from modulink.core import create_modulink

        modulink = create_modulink()

        def test_chain(ctx):
            return ctx

        try:
            result = modulink.connect(
                ConnectionType.HTTP, test_chain, app=Mock(), method="GET", path="/test"
            )
            print("✅ Connect succeeded")
            print(f"✅ Mock handler called: {mock_handler.called}")
            print(f"✅ Mock handler call count: {mock_handler.call_count}")
            return True
        except Exception as e:
            print(f"❌ Connect failed: {e}")
            return False


if __name__ == "__main__":
    success = test_mock_fix()
    if success:
        print("\n🎉 Mock fix works! The tests should pass once updated.")
    else:
        print("\n💥 Mock fix failed!")
