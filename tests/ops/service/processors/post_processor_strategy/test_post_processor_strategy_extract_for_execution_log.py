from unittest.mock import create_autospec, patch

from requests import Response

from fides.api.schemas.saas.strategy_configuration import (
    ExtractForExecutionLogPostProcessorConfiguration,
)
from fides.api.service.execution_context import collect_execution_log_messages
from fides.api.service.processors.post_processor_strategy.post_processor_strategy_extract_for_execution_log import (
    ExtractForExecutionLogPostProcessorStrategy,
)


class TestExtractForExecutionLogPostProcessorStrategy:
    """Test the extract_for_execution_log postprocessor"""

    def test_extract_from_various_paths(self):
        """Test extracting values from simple and nested paths in response contents"""
        # Test simple path
        config = ExtractForExecutionLogPostProcessorConfiguration(path="user.email")
        data = {"user": {"email": "test@example.com", "name": "Test User"}}

        mock_response = create_autospec(Response)
        mock_response.content = data
        mock_response.json.return_value = data

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        with collect_execution_log_messages() as messages:
            result = processor.process(data, response=mock_response)
            assert result == data
            assert len(messages) == 1
            assert messages[0] == "test@example.com"

        # Test nested array path
        config = ExtractForExecutionLogPostProcessorConfiguration(path="users.0.email")
        data = {
            "users": [
                {"email": "first@example.com", "name": "First User"},
                {"email": "second@example.com", "name": "Second User"},
            ]
        }

        mock_response = create_autospec(Response)
        mock_response.content = data
        mock_response.json.return_value = data

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        with collect_execution_log_messages() as messages:
            result = processor.process(data, response=mock_response)
            assert result == data
            assert len(messages) == 1
            assert messages[0] == "first@example.com"

    def test_extract_entire_contents_when_no_path(self):
        """Test extracting entire response contents when no path is specified"""
        config = ExtractForExecutionLogPostProcessorConfiguration()  # No path
        data = {"status": "success", "count": 42}

        # Create mock response with contents
        mock_response = create_autospec(Response)
        mock_response.content = {"status": "success", "count": 42}
        mock_response.json.return_value = {"status": "success", "count": 42}

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        with collect_execution_log_messages() as messages:
            result = processor.process(data, response=mock_response)

            assert result == data
            # Should capture entire contents as string
            expected_string = str(mock_response.content)
            assert len(messages) == 1
            assert messages[0] == expected_string

    def test_missing_path_in_data(self):
        """Test handling of missing paths gracefully"""
        config = ExtractForExecutionLogPostProcessorConfiguration(
            path="nonexistent.field"
        )
        data = {"existing": "data"}

        # Create mock response with contents
        mock_response = create_autospec(Response)
        mock_response.content = {"existing": "data"}
        mock_response.json.return_value = {"existing": "data"}

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        with collect_execution_log_messages() as messages:
            result = processor.process(data, response=mock_response)

            # Should still return original data
            assert result == data

            # Should not capture any messages
            assert len(messages) == 0

    def test_no_response_contents_handling(self):
        """Test handling when response.content is not available"""
        config = ExtractForExecutionLogPostProcessorConfiguration(path="any.path")
        data = {"some": "data"}

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        with collect_execution_log_messages() as messages:
            # No response provided
            result = processor.process(data)

            # Should return data unchanged
            assert result == data

            # Should not capture any messages
            assert len(messages) == 0

    def test_deep_nested_extraction(self):
        """Test extracting from deeply nested structures"""
        config = ExtractForExecutionLogPostProcessorConfiguration(
            path="api.result.user.settings.enabled"
        )
        data = {"api": {"result": {"user": {"settings": {"enabled": True}}}}}

        mock_response = create_autospec(Response)
        mock_response.content = data
        mock_response.json.return_value = data

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        with collect_execution_log_messages() as messages:
            result = processor.process(data, response=mock_response)
            assert result == data
            assert len(messages) == 1
            assert messages[0] == "True"

    def test_error_handling(self):
        """Test that errors are captured in execution context"""
        config = ExtractForExecutionLogPostProcessorConfiguration(path="test.path")
        data = {"test": "data"}

        # Create mock response with contents
        mock_response = create_autospec(Response)
        mock_response.content = {"test": "data"}
        mock_response.json.return_value = {"test": "data"}

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        # Mock pydash.get to raise an exception
        with collect_execution_log_messages() as messages:
            with patch(
                "fides.api.service.processors.post_processor_strategy.post_processor_strategy_extract_for_execution_log.pydash.get",
                side_effect=Exception("Test error"),
            ):
                result = processor.process(data, response=mock_response)

                # Should still return original data
                assert result == data

                # Should capture error in execution context
                assert len(messages) == 1
                assert (
                    "Error in extract_for_execution_log postprocessor: Test error"
                    in messages[0]
                )

    def test_data_handling_and_response_contents(self):
        """Test that postprocessor is non-destructive and uses response.content correctly"""

        config = ExtractForExecutionLogPostProcessorConfiguration(path="user.id")
        original_data = {
            "user": {"id": 12345, "email": "test@example.com"},
            "metadata": {"timestamp": "2023-01-01"},
        }

        mock_response = create_autospec(Response)
        mock_response.content = original_data
        mock_response.json.return_value = original_data

        processor = ExtractForExecutionLogPostProcessorStrategy(configuration=config)

        with collect_execution_log_messages() as messages:
            result = processor.process(original_data, response=mock_response)
            # Data should be completely unchanged
            assert result == original_data
            assert result is original_data  # Should be the same object
            assert len(messages) == 1
            assert messages[0] == "12345"
