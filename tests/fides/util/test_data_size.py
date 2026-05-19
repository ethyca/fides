import json

from loguru import logger

from fides.api.util.data_size import calculate_data_size


class TestCalculateDataSize:
    """Tests for util.data_size.calculate_data_size and related helpers."""

    def test_calculate_data_size_empty_data(self):
        result = calculate_data_size([])
        assert result == 0

    def test_calculate_data_size_small_dataset_exact_match(self):
        test_data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
        json_str = json.dumps(test_data, separators=(",", ":"))
        expected_size = len(json_str.encode("utf-8"))
        assert calculate_data_size(test_data) == expected_size

    def test_calculate_data_size_large_dataset_estimation_accuracy(self):
        large_data = [
            {"id": i, "name": f"user_{i}", "email": f"user{i}@example.com"}
            for i in range(2000)
        ]
        estimated_size = calculate_data_size(large_data)
        actual_size = len(json.dumps(large_data, separators=(",", ":")).encode("utf-8"))
        variance_ratio = abs(estimated_size - actual_size) / actual_size
        logger.info(
            "Estimated size: {} bytes, actual: {} bytes (variance {:.2%})",
            estimated_size,
            actual_size,
            variance_ratio,
        )
        assert variance_ratio < 0.05  # within 5%

    def test_calculate_data_size_unicode_precision(self):
        unicode_data = [
            {"name": "José", "city": "São Paulo", "emoji": "🚀"},
            {"name": "François", "description": "测试数据"},
        ]
        expected_size = len(
            json.dumps(unicode_data, separators=(",", ":")).encode("utf-8")
        )
        assert calculate_data_size(unicode_data) == expected_size

    def test_calculate_data_size_nested_structures_exact(self):
        complex_data = [
            {
                "user": {
                    "id": 1,
                    "profile": {
                        "name": "Alice",
                        "settings": {"theme": "dark", "notifications": True},
                    },
                    "history": [
                        {"action": "login", "timestamp": "2024-01-01T10:00:00"},
                        {
                            "action": "view_page",
                            "timestamp": "2024-01-01T10:05:00",
                            "page": "/dashboard",
                        },
                    ],
                },
                "metadata": {
                    "version": "1.0",
                    "tags": ["premium", "active"],
                    "score": 95.5,
                },
            }
        ]
        expected_size = len(
            json.dumps(complex_data, separators=(",", ":")).encode("utf-8")
        )
        assert calculate_data_size(complex_data) == expected_size
