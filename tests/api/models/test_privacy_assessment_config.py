"""Tests for the PrivacyAssessmentConfig model."""

import pytest

from fides.api.models.privacy_assessment_config import (
    DEFAULT_ASSESSMENT_MODEL,
    DEFAULT_CHAT_MODEL,
    PrivacyAssessmentConfig,
)


class TestPrivacyAssessmentConfigModelMethods:
    """Tests for the PrivacyAssessmentConfig class methods."""

    def test_get_assessment_model_with_none_config(self):
        """Test that None config returns the default assessment model."""
        result = PrivacyAssessmentConfig.get_assessment_model(None)
        assert result == DEFAULT_ASSESSMENT_MODEL

    def test_get_assessment_model_with_no_override(self, db):
        """Test that config without override returns the default model."""
        config = PrivacyAssessmentConfig(
            assessment_model_override=None,
        )
        db.add(config)
        db.commit()

        result = PrivacyAssessmentConfig.get_assessment_model(config)
        assert result == DEFAULT_ASSESSMENT_MODEL

    def test_get_assessment_model_with_empty_override(self, db):
        """Test that empty string override returns the default model."""
        config = PrivacyAssessmentConfig(
            assessment_model_override="",
        )
        db.add(config)
        db.commit()

        result = PrivacyAssessmentConfig.get_assessment_model(config)
        assert result == DEFAULT_ASSESSMENT_MODEL

    def test_get_assessment_model_with_override(self, db):
        """Test that config with override returns the custom model."""
        custom_model = "custom/my-assessment-model"
        config = PrivacyAssessmentConfig(
            assessment_model_override=custom_model,
        )
        db.add(config)
        db.commit()

        result = PrivacyAssessmentConfig.get_assessment_model(config)
        assert result == custom_model

    def test_get_chat_model_with_none_config(self):
        """Test that None config returns the default chat model."""
        result = PrivacyAssessmentConfig.get_chat_model(None)
        assert result == DEFAULT_CHAT_MODEL

    def test_get_chat_model_with_no_override(self, db):
        """Test that config without override returns the default model."""
        config = PrivacyAssessmentConfig(
            chat_model_override=None,
        )
        db.add(config)
        db.commit()

        result = PrivacyAssessmentConfig.get_chat_model(config)
        assert result == DEFAULT_CHAT_MODEL

    def test_get_chat_model_with_empty_override(self, db):
        """Test that empty string override returns the default model."""
        config = PrivacyAssessmentConfig(
            chat_model_override="",
        )
        db.add(config)
        db.commit()

        result = PrivacyAssessmentConfig.get_chat_model(config)
        assert result == DEFAULT_CHAT_MODEL

    def test_get_chat_model_with_override(self, db):
        """Test that config with override returns the custom model."""
        custom_model = "custom/my-chat-model"
        config = PrivacyAssessmentConfig(
            chat_model_override=custom_model,
        )
        db.add(config)
        db.commit()

        result = PrivacyAssessmentConfig.get_chat_model(config)
        assert result == custom_model

    def test_both_models_independent(self, db):
        """Test that assessment and chat model overrides work independently."""
        assessment_model = "custom/assessment"
        config = PrivacyAssessmentConfig(
            assessment_model_override=assessment_model,
            chat_model_override=None,
        )
        db.add(config)
        db.commit()

        # Assessment should use override
        assert PrivacyAssessmentConfig.get_assessment_model(config) == assessment_model
        # Chat should use default
        assert PrivacyAssessmentConfig.get_chat_model(config) == DEFAULT_CHAT_MODEL

    def test_both_models_with_overrides(self, db):
        """Test that both models can be overridden independently."""
        assessment_model = "custom/assessment"
        chat_model = "custom/chat"
        config = PrivacyAssessmentConfig(
            assessment_model_override=assessment_model,
            chat_model_override=chat_model,
        )
        db.add(config)
        db.commit()

        assert PrivacyAssessmentConfig.get_assessment_model(config) == assessment_model
        assert PrivacyAssessmentConfig.get_chat_model(config) == chat_model
