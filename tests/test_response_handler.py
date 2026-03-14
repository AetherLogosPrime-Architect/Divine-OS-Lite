"""
Tests for response handler module.
Verify LLM response parsing and tool call extraction.
"""

import pytest
from src.divineos.response_handler import ResponseHandler, ToolCall


class TestToolCallDefinition:
    """Test ToolCall dataclass."""

    def test_tool_call_creation(self) -> None:
        """Test creating a tool call."""
        call = ToolCall(
            tool_name="search",
            parameters={"query": "test"},
            raw_text="TOOL: search(query=test)",
        )

        assert call.tool_name == "search"
        assert call.parameters == {"query": "test"}

    def test_tool_call_validation_empty_name(self) -> None:
        """Test validation rejects empty name."""
        with pytest.raises(ValueError):
            ToolCall(
                tool_name="",
                parameters={},
                raw_text="",
            )

    def test_tool_call_validation_non_dict_params(self) -> None:
        """Test validation rejects non-dict parameters."""
        with pytest.raises(ValueError):
            ToolCall(
                tool_name="test",
                parameters="not_dict",
                raw_text="",
            )


class TestResponseHandlerBasics:
    """Test basic response handler functionality."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_init(self, handler: ResponseHandler) -> None:
        """Test initialization."""
        assert handler.tool_calls_parsed == 0
        assert handler.responses_processed == 0

    def test_parse_empty_response(self, handler: ResponseHandler) -> None:
        """Test parsing empty response."""
        result = handler.parse_response("")

        assert result["success"] is False
        assert result["tool_calls"] == []

    def test_parse_simple_text(self, handler: ResponseHandler) -> None:
        """Test parsing simple text response."""
        result = handler.parse_response("Hello, how can I help?")

        assert result["success"] is True
        assert result["text"] == "Hello, how can I help?"
        assert result["tool_calls"] == []
        assert result["has_tool_calls"] is False


class TestToolCallExtraction:
    """Test tool call extraction."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_extract_single_tool_call(self, handler: ResponseHandler) -> None:
        """Test extracting single tool call."""
        response = "Let me search for that. TOOL: search(query=test)"
        result = handler.parse_response(response)

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0].tool_name == "search"
        assert result["tool_calls"][0].parameters["query"] == "test"

    def test_extract_multiple_tool_calls(
        self, handler: ResponseHandler
    ) -> None:
        """Test extracting multiple tool calls."""
        response = (
            "First TOOL: search(query=test) "
            "then TOOL: analyze(data=result)"
        )
        result = handler.parse_response(response)

        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0].tool_name == "search"
        assert result["tool_calls"][1].tool_name == "analyze"

    def test_extract_tool_call_with_multiple_params(
        self, handler: ResponseHandler
    ) -> None:
        """Test extracting tool call with multiple parameters."""
        response = "TOOL: search(query=test, limit=10, sort=date)"
        result = handler.parse_response(response)

        assert len(result["tool_calls"]) == 1
        call = result["tool_calls"][0]
        assert call.parameters["query"] == "test"
        assert call.parameters["limit"] == 10
        assert call.parameters["sort"] == "date"

    def test_extract_tool_call_with_quoted_params(
        self, handler: ResponseHandler
    ) -> None:
        """Test extracting tool call with quoted parameters."""
        response = 'TOOL: search(query="hello world", limit=5)'
        result = handler.parse_response(response)

        assert len(result["tool_calls"]) == 1
        call = result["tool_calls"][0]
        assert call.parameters["query"] == "hello world"
        assert call.parameters["limit"] == 5


class TestParameterParsing:
    """Test parameter parsing."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_parse_string_param(self, handler: ResponseHandler) -> None:
        """Test parsing string parameter."""
        params = handler._parse_parameters('query=test')
        assert params["query"] == "test"

    def test_parse_int_param(self, handler: ResponseHandler) -> None:
        """Test parsing integer parameter."""
        params = handler._parse_parameters('limit=10')
        assert params["limit"] == 10
        assert isinstance(params["limit"], int)

    def test_parse_float_param(self, handler: ResponseHandler) -> None:
        """Test parsing float parameter."""
        params = handler._parse_parameters('threshold=0.5')
        assert params["threshold"] == 0.5
        assert isinstance(params["threshold"], float)

    def test_parse_bool_param(self, handler: ResponseHandler) -> None:
        """Test parsing boolean parameter."""
        params = handler._parse_parameters('enabled=true, disabled=false')
        assert params["enabled"] is True
        assert params["disabled"] is False

    def test_parse_none_param(self, handler: ResponseHandler) -> None:
        """Test parsing None parameter."""
        params = handler._parse_parameters('value=None')
        assert params["value"] is None

    def test_parse_quoted_string(self, handler: ResponseHandler) -> None:
        """Test parsing quoted string."""
        params = handler._parse_parameters('text="hello world"')
        assert params["text"] == "hello world"

    def test_parse_multiple_params(self, handler: ResponseHandler) -> None:
        """Test parsing multiple parameters."""
        params = handler._parse_parameters(
            'name=test, count=5, enabled=true'
        )
        assert params["name"] == "test"
        assert params["count"] == 5
        assert params["enabled"] is True

    def test_parse_empty_params(self, handler: ResponseHandler) -> None:
        """Test parsing empty parameters."""
        params = handler._parse_parameters('')
        assert params == {}


class TestValueParsing:
    """Test value parsing."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_parse_string_value(self, handler: ResponseHandler) -> None:
        """Test parsing string value."""
        value = handler._parse_value("hello")
        assert value == "hello"
        assert isinstance(value, str)

    def test_parse_quoted_string_value(self, handler: ResponseHandler) -> None:
        """Test parsing quoted string value."""
        value = handler._parse_value('"hello world"')
        assert value == "hello world"

    def test_parse_int_value(self, handler: ResponseHandler) -> None:
        """Test parsing integer value."""
        value = handler._parse_value("42")
        assert value == 42
        assert isinstance(value, int)

    def test_parse_float_value(self, handler: ResponseHandler) -> None:
        """Test parsing float value."""
        value = handler._parse_value("3.14")
        assert value == 3.14
        assert isinstance(value, float)

    def test_parse_bool_true_value(self, handler: ResponseHandler) -> None:
        """Test parsing boolean true value."""
        value = handler._parse_value("true")
        assert value is True

    def test_parse_bool_false_value(self, handler: ResponseHandler) -> None:
        """Test parsing boolean false value."""
        value = handler._parse_value("false")
        assert value is False

    def test_parse_none_value(self, handler: ResponseHandler) -> None:
        """Test parsing None value."""
        value = handler._parse_value("None")
        assert value is None


class TestTextExtraction:
    """Test text extraction from response."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_extract_text_no_tools(self, handler: ResponseHandler) -> None:
        """Test extracting text when no tool calls."""
        text = handler._extract_text("Hello world")
        assert text == "Hello world"

    def test_extract_text_with_tools(self, handler: ResponseHandler) -> None:
        """Test extracting text with tool calls."""
        response = "Let me look. TOOL: search(query=test) Found it!"
        text = handler._extract_text(response)
        assert "TOOL:" not in text
        assert "Let me look" in text
        assert "Found it" in text

    def test_extract_text_multiple_tools(
        self, handler: ResponseHandler
    ) -> None:
        """Test extracting text with multiple tool calls."""
        response = (
            "First TOOL: search(query=test) "
            "then TOOL: analyze(data=result) done"
        )
        text = handler._extract_text(response)
        assert "TOOL:" not in text
        assert "First" in text
        assert "done" in text


class TestToolResultFormatting:
    """Test tool result formatting."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_format_string_result(self, handler: ResponseHandler) -> None:
        """Test formatting string result."""
        result = handler.format_tool_result("search", "Found 5 results")

        assert "[TOOL RESULT]" in result
        assert "search" in result
        assert "SUCCESS" in result
        assert "Found 5 results" in result

    def test_format_dict_result(self, handler: ResponseHandler) -> None:
        """Test formatting dict result."""
        result = handler.format_tool_result(
            "search", {"count": 5, "items": ["a", "b"]}
        )

        assert "[TOOL RESULT]" in result
        assert "search" in result

    def test_format_failed_result(self, handler: ResponseHandler) -> None:
        """Test formatting failed result."""
        result = handler.format_tool_result(
            "search", "Error occurred", success=False
        )

        assert "FAILED" in result
        assert "Error occurred" in result


class TestStatistics:
    """Test statistics tracking."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_stats_initial(self, handler: ResponseHandler) -> None:
        """Test initial statistics."""
        stats = handler.get_stats()

        assert stats["responses_processed"] == 0
        assert stats["tool_calls_parsed"] == 0

    def test_stats_after_parsing(self, handler: ResponseHandler) -> None:
        """Test statistics after parsing."""
        handler.parse_response("TOOL: search(query=test)")
        stats = handler.get_stats()

        assert stats["responses_processed"] == 1
        assert stats["tool_calls_parsed"] == 1

    def test_stats_avg_tool_calls(self, handler: ResponseHandler) -> None:
        """Test average tool calls calculation."""
        handler.parse_response("TOOL: search(query=test)")
        handler.parse_response("TOOL: a(x=1) TOOL: b(y=2)")

        stats = handler.get_stats()

        assert stats["responses_processed"] == 2
        assert stats["tool_calls_parsed"] == 3
        assert stats["avg_tool_calls_per_response"] == 1.5

    def test_reset_stats(self, handler: ResponseHandler) -> None:
        """Test resetting statistics."""
        handler.parse_response("TOOL: search(query=test)")
        assert handler.responses_processed == 1

        handler.reset_stats()
        assert handler.responses_processed == 0
        assert handler.tool_calls_parsed == 0


class TestEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def handler(self) -> ResponseHandler:
        """Create response handler instance."""
        return ResponseHandler()

    def test_malformed_tool_call(self, handler: ResponseHandler) -> None:
        """Test handling malformed tool call."""
        response = "TOOL: search(query=test"  # Missing closing paren
        result = handler.parse_response(response)

        # Should not extract malformed call
        assert len(result["tool_calls"]) == 0

    def test_tool_call_with_spaces(self, handler: ResponseHandler) -> None:
        """Test tool call with extra spaces."""
        response = "TOOL:  search  (  query = test  )"
        result = handler.parse_response(response)

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0].tool_name == "search"

    def test_nested_quotes(self, handler: ResponseHandler) -> None:
        """Test handling nested quotes."""
        response = 'TOOL: search(query="test\'s value")'
        result = handler.parse_response(response)

        assert len(result["tool_calls"]) == 1

    def test_very_long_response(self, handler: ResponseHandler) -> None:
        """Test handling very long response."""
        response = "x" * 10000 + " TOOL: search(query=test)"
        result = handler.parse_response(response)

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0].tool_name == "search"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
