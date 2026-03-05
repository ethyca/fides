import { Form, Input, Switch, Tooltip } from "fidesui";
import { useEffect } from "react";

import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";

export interface LlmModelSelectorProps {
  /**
   * Don't render anything. Use this when the parent decides the component
   * shouldn't be shown (e.g., feature flag off, infrastructure monitor, etc.)
   */
  skip?: boolean;
  /**
   * Whether to show the "Use LLM classifier" switch toggle.
   * - true (default): Shows switch + conditionally shows model field when switch is on
   * - false: Just shows the model override field directly (for settings modals)
   */
  showSwitch?: boolean;
  /**
   * Current form value for the use_llm_classifier switch.
   * Required when showSwitch=true to conditionally show the model override field.
   */
  useLlmClassifier?: boolean;
  /** Form field name for the switch - defaults to "use_llm_classifier" */
  switchName?: string;
  /** Form field name for model override - defaults to "llm_model_override" */
  modelOverrideName?: string;
  /** Label for the model override field - defaults to "Model override" */
  modelOverrideLabel?: string;
  /** Tooltip for the model override field */
  modelOverrideTooltip?: string;
  /** Placeholder for the model override input */
  modelOverridePlaceholder?: string;
  /** Test ID for the model override input (defaults to modelOverrideName) */
  modelOverrideTestId?: string;
}

const SWITCH_LABEL = "Use LLM classifier";
const SWITCH_TOOLTIP_ENABLED =
  "Enable LLM-based classification for assets that cannot be identified by Compass";
const SWITCH_TOOLTIP_DISABLED =
  "LLM classifier is currently disabled for this server. Contact Ethyca support to learn more.";
const DEFAULT_MODEL_OVERRIDE_LABEL = "Model override";
const DEFAULT_MODEL_OVERRIDE_TOOLTIP =
  "Optionally specify a custom model to use for LLM classification";
const DEFAULT_MODEL_OVERRIDE_PLACEHOLDER =
  "e.g., openrouter/google/gemini-2.5-flash";

/**
 * Shared component for LLM classification settings.
 * Used in website monitors, database monitors, privacy assessments, and other features.
 *
 * This component:
 * - Fetches server configuration to check if LLM classifier is enabled
 * - Optionally renders a switch to enable/disable LLM classification (showSwitch=true)
 * - Shows a model override field (conditionally when switch is on, or always when showSwitch=false)
 * - Handles disabled state when server doesn't support LLM
 */
export const LlmModelSelector = ({
  skip = false,
  showSwitch = true,
  useLlmClassifier,
  switchName = "use_llm_classifier",
  modelOverrideName = "llm_model_override",
  modelOverrideLabel = DEFAULT_MODEL_OVERRIDE_LABEL,
  modelOverrideTooltip = DEFAULT_MODEL_OVERRIDE_TOOLTIP,
  modelOverridePlaceholder = DEFAULT_MODEL_OVERRIDE_PLACEHOLDER,
  modelOverrideTestId,
}: LlmModelSelectorProps) => {
  const form = Form.useFormInstance();

  // Fetch server configuration to check LLM capability
  const { data: appConfig, isLoading } = useGetConfigurationSettingsQuery(
    { api_set: false },
    { skip },
  );

  const serverSupportsLlmClassifier =
    !!appConfig?.detection_discovery?.llm_classifier_enabled;

  // Reset switch to false if server doesn't support LLM classifier
  // This ensures we don't show a checked toggle for an unavailable feature
  useEffect(() => {
    if (!skip && !isLoading && !serverSupportsLlmClassifier && showSwitch) {
      form?.setFieldValue(switchName, false);
    }
  }, [
    skip,
    isLoading,
    serverSupportsLlmClassifier,
    showSwitch,
    form,
    switchName,
  ]);

  if (skip) {
    return null;
  }

  // Model field visibility:
  // - With switch: show when switch is on AND server supports LLM
  // - Without switch: always show
  const showModelField = showSwitch
    ? useLlmClassifier && serverSupportsLlmClassifier
    : true;

  const modelFieldTestId = modelOverrideTestId
    ? `input-${modelOverrideTestId}`
    : `input-${modelOverrideName}`;

  return (
    <>
      {showSwitch && (
        <Form.Item
          name={switchName}
          label={SWITCH_LABEL}
          tooltip={
            !serverSupportsLlmClassifier
              ? SWITCH_TOOLTIP_DISABLED
              : SWITCH_TOOLTIP_ENABLED
          }
          valuePropName="checked"
        >
          <Switch
            data-testid={`input-${switchName}`}
            disabled={!serverSupportsLlmClassifier}
          />
        </Form.Item>
      )}
      <Form.Item
        name={modelOverrideName}
        label={
          !serverSupportsLlmClassifier ? (
            <Tooltip title={SWITCH_TOOLTIP_DISABLED}>
              <span>{modelOverrideLabel}</span>
            </Tooltip>
          ) : (
            modelOverrideLabel
          )
        }
        tooltip={serverSupportsLlmClassifier ? modelOverrideTooltip : undefined}
        hidden={!showModelField}
      >
        <Input
          data-testid={modelFieldTestId}
          placeholder={modelOverridePlaceholder}
          disabled={!serverSupportsLlmClassifier}
        />
      </Form.Item>
    </>
  );
};

export default LlmModelSelector;
