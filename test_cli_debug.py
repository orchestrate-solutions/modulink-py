#!/usr/bin/env python3
"""Test to verify CLI command execution"""

from unittest.mock import Mock, patch
from modulink.connect import _handle_cli_connection

@patch('modulink.connect.click')
@patch('modulink.connect.datetime') 
def test_cli_execution(mock_datetime, mock_click):
    """Test that verifies CLI command execution and print calls"""
    print("Testing CLI command execution with patches...")
    
    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"
    
    # Set up click mock to behave like real click
    def mock_option(*args, **kwargs):
        def decorator(func):
            return func  # Just return the function unchanged
        return decorator
    
    mock_click.option = mock_option
    
    # Mock modulink
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "cli", "executed": True}
    
    mock_chain_fn = Mock(return_value={"result": "cli_success"})
    
    mock_cli_group = Mock()
    captured_command = None
    
    def capture_command(name):
        def decorator(func):
            nonlocal captured_command
            captured_command = func
            return func
        return decorator
    
    mock_cli_group.command = capture_command
    
    # Setup CLI connection
    kwargs = {
        "cli_group": mock_cli_group,
        "command_name": "test-cmd"
    }
    
    _handle_cli_connection(mock_modulink, mock_chain_fn, **kwargs)
    
    print(f"Captured command: {captured_command}")
    print(f"Chain function: {mock_chain_fn}")
    
    # Execute the captured command
    if captured_command:
        print("Executing captured command without print mock...")
        try:
            captured_command("test.txt")
            print("Command executed successfully")
        except Exception as e:
            print(f"Error executing command: {e}")
        
        # Now test with mock print
        print("Testing with mock print...")
        with patch('builtins.print') as mock_print:
            try:
                captured_command("test.txt")
            except Exception as e:
                print(f"Error with mock print: {e}")
            # Check calls within the context manager
            print(f"Print call count inside context: {mock_print.call_count}")
            print(f"Print calls inside context: {mock_print.call_args_list}")
        
        print("Testing complete")

if __name__ == "__main__":
    test_cli_execution()

if __name__ == "__main__":
    test_cli_execution()
