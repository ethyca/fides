import { Form, Input, Tooltip } from "fidesui";
import React from "react";

export interface LlmModelOverrideFieldProps {
  /** Form field name - defaults to "llm_model_override" */
  name?: string;
  /** Label text - defaults to "LLM model override" */
  label?: string;
  /** Tooltip when field is enabled */
  tooltip?: string;
  /** Tooltip when field is disabled (e.g., server doesn't support) */
  disabledTooltip?: string;
  /** Whether the field is disabled */
  disabled?: boolean;
  /** Placeholder text (e.g., showing the default model) */
  placeholder?: string;
  /** Test ID suffix - full ID will be "input-{testId}" */
  testId?: string;
}

/**
 * Shared form field component for LLM model override settings.
 * Used across website monitors, database monitors, and privacy assessments.
 *
 * Wraps an Input in a Form.Item with consistent styling and behavior:
 * - Shows tooltip explaining the field purpose
 * - Can show a different tooltip when disabled (e.g., when server doesn't support LLM)
 * - Placeholder can show the default model value
 */
export const LlmModelOverrideField: React.FC<LlmModelOverrideFieldProps> = ({
  name = "llm_model_override",
  label = "LLM model override",
  tooltip = "Optionally specify a custom model to use for LLM classification. Leave empty to use the default.",
  disabledTooltip,
  disabled = false,
  placeholder,
  testId,
}) => {
  const effectiveTooltip = disabled && disabledTooltip ? disabledTooltip : tooltip;
  const dataTestId = testId ? `input-${testId}` : `input-${name}`;

  // When disabled with a special tooltip, wrap the label in a Tooltip
  // Otherwise, use Form.Item's built-in tooltip
  const labelContent =
    disabled && disabledTooltip ? (
      <Tooltip title={disabledTooltip}>
        <span>{label}</span>
      </Tooltip>
    ) : (
      label
    );

  return (
    <Form.Item
      name={name}
      label={labelContent}
      tooltip={!(disabled && disabledTooltip) ? effectiveTooltip : undefined}
    >
      <Input
        data-testid={dataTestId}
        placeholder={placeholder}
        disabled={disabled}
      />
    </Form.Item>
  );
};

export default LlmModelOverrideField;
