import threading

from fides.api.service.execution_context import (
    add_execution_log_message,
    collect_execution_log_messages,
    get_execution_log_messages,
)


class TestExecutionContext:

    def test_collect_execution_log_messages_context_manager(self):
        """Test that collect_execution_log_messages can be used as a context manager"""
        with collect_execution_log_messages() as messages:
            add_execution_log_message("Test message 1")
            add_execution_log_message("Test message 2")

        # Messages should be collected in the list
        assert messages == ["Test message 1", "Test message 2"]

    def test_nested_contexts_are_isolated(self):
        """Test that nested contexts don't interfere with each other"""
        with collect_execution_log_messages() as outer_messages:
            add_execution_log_message("Outer message")

            with collect_execution_log_messages() as inner_messages:
                add_execution_log_message("Inner message")

                assert inner_messages == ["Inner message"]
                assert get_execution_log_messages() == ["Inner message"]

            # Back to outer context - should only have outer message
            assert outer_messages == ["Outer message"]
            assert get_execution_log_messages() == ["Outer message"]

    def test_no_context_active(self):
        """Test that adding messages without context doesn't error but logs warning"""
        # This should not raise exceptions but should log an error
        add_execution_log_message("Should be ignored")

        # Should return empty when no context is active
        assert get_execution_log_messages() == []

    def test_multiple_messages_in_same_context(self):
        """Test collecting multiple messages in the same context"""
        with collect_execution_log_messages() as messages:
            add_execution_log_message("Message 1")
            add_execution_log_message("Message 2")
            add_execution_log_message("Message 3")

        assert len(messages) == 3
        assert messages == ["Message 1", "Message 2", "Message 3"]

    def test_context_isolation_across_threads(self):
        """Test that context variables are isolated across different execution contexts"""

        results = {}

        def worker(worker_id):
            with collect_execution_log_messages() as messages:
                add_execution_log_message(f"Worker {worker_id} message")
                results[worker_id] = messages.copy()

        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Each worker should have its own isolated messages
        assert results[0] == ["Worker 0 message"]
        assert results[1] == ["Worker 1 message"]
        assert results[2] == ["Worker 2 message"]

    def test_get_execution_log_messages_returns_copy(self):
        """Test that get_execution_log_messages returns a copy, not the original list"""
        with collect_execution_log_messages() as messages:
            add_execution_log_message("Original message")

            # Get a copy of messages
            retrieved_messages = get_execution_log_messages()

            # Modify the copy
            retrieved_messages.append("Modified message")

            # Original messages should be unchanged
            assert messages == ["Original message"]
            assert len(messages) == 1

    def test_messages_cleared_after_context_exit(self):
        """Test that messages are not accessible after context exits"""
        with collect_execution_log_messages() as messages:
            add_execution_log_message("Test message")
            assert messages == ["Test message"]

        # After context exits, should return empty
        assert get_execution_log_messages() == []

    def test_empty_message_handling(self):
        """Test that empty and whitespace-only messages are excluded"""
        with collect_execution_log_messages() as messages:
            add_execution_log_message("")  # Should be excluded
            add_execution_log_message("   ")  # Should be excluded (whitespace only)
            add_execution_log_message("\t\n  ")  # Should be excluded (whitespace only)
            add_execution_log_message("real message")  # Should be included
            add_execution_log_message(
                "  another message  "
            )  # Should be included (has content)

            # Only non-empty messages should be captured
            assert len(messages) == 2
            assert messages == ["real message", "another message"]
