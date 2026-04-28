"""Simple test script to verify MCP system works"""

import asyncio
import sys
import json

# Test imports
try:
    from app.mcp.browser_engine import browser_engine
    from app.mcp.page_state import page_state_manager
    from app.mcp.security import SecurityValidator
    from app.services.mcp_service import mcp_service
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

async def test_page_state():
    """Test page state manager"""
    print("\n--- Testing Page State Manager ---")

    # Create session
    state = page_state_manager.create_session("test-session")
    print(f"✓ Created session: {state.session_id}")

    # Update state
    page_state_manager.update_state(
        "test-session",
        current_url="http://localhost:3001/ai-demo",
        page_title="Demo Page",
    )
    print("✓ Updated page state")

    # Get state
    retrieved = page_state_manager.get_session("test-session")
    assert retrieved is not None
    print(f"✓ Retrieved state: {retrieved.current_url}")


def test_security_validator():
    """Test security validator"""
    print("\n--- Testing Security Validator ---")

    # Valid selectors
    valid_selectors = [
        "button.submit",
        "[data-testid=reset-btn]",
        "input[type=text]",
        ".form-group",
        "#submit-button",
    ]

    for selector in valid_selectors:
        is_valid, error = SecurityValidator.validate_selector(selector)
        assert is_valid, f"Failed to validate '{selector}': {error}"
    print(f"✓ Validated {len(valid_selectors)} selectors")

    # Invalid selectors
    invalid_selectors = [
        "script alert('xss')",
        "iframe src=evil.com",
    ]

    for selector in invalid_selectors:
        is_valid, error = SecurityValidator.validate_selector(selector)
        assert not is_valid, f"Should have rejected '{selector}'"
    print(f"✓ Rejected {len(invalid_selectors)} invalid selectors")

    # Valid URL paths
    valid_paths = ["/ai-demo", "/ai-demo/test"]
    for path in valid_paths:
        is_valid, error = SecurityValidator.validate_url_path(path)
        assert is_valid, f"Failed to validate '{path}': {error}"
    print(f"✓ Validated {len(valid_paths)} URL paths")

    # Invalid URL paths
    invalid_paths = ["/admin", "/api/secret", "javascript:alert('xss')"]
    for path in invalid_paths:
        is_valid, error = SecurityValidator.validate_url_path(path)
        assert not is_valid, f"Should have rejected '{path}'"
    print(f"✓ Rejected {len(invalid_paths)} invalid URL paths")


def test_mcp_service():
    """Test MCP service configuration"""
    print("\n--- Testing MCP Service ---")

    # Check available tools
    assert len(mcp_service.AVAILABLE_TOOLS) == 6
    print(f"✓ {len(mcp_service.AVAILABLE_TOOLS)} tools available:")
    for tool in mcp_service.AVAILABLE_TOOLS:
        print(f"  - {tool}")

    # Check tool definitions
    assert len(mcp_service.TOOL_DEFINITIONS) == 6
    print(f"✓ {len(mcp_service.TOOL_DEFINITIONS)} tool definitions configured")

    # Check system prompt
    prompt = mcp_service._build_system_prompt()
    assert "click" in prompt
    assert "screenshot" in prompt
    print("✓ System prompt configured")


async def main():
    """Run all tests"""
    print("=" * 50)
    print("MCP System Test Suite")
    print("=" * 50)

    try:
        # Test security validator (no async needed)
        test_security_validator()
        test_mcp_service()

        # Test page state (async)
        await test_page_state()

        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
