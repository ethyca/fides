import {
  Alert,
  Button,
  Flex,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Switch,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useState } from "react";

import { useGetChatChannelsQuery } from "~/features/chat-provider/chatProvider.slice";
import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { parseCronExpression } from "~/features/digests/helpers/cronHelpers";

import {
  useGetAssessmentConfigDefaultsQuery,
  useGetAssessmentConfigQuery,
  useTestSlackChannelMutation,
  useUpdateAssessmentConfigMutation,
} from "./privacy-assessments.slice";

const { Text } = Typography;

// Frequency options for the schedule picker
const FREQUENCY_OPTIONS = [
  { label: "Daily", value: "daily", cron: "0 9 * * *" },
  { label: "Weekly (Mondays)", value: "weekly", cron: "0 9 * * 1" },
  { label: "Monthly (1st)", value: "monthly", cron: "0 9 1 * *" },
  { label: "Yearly (Jan 1st)", value: "yearly", cron: "0 9 1 1 *" },
];

interface AssessmentSettingsModalProps {
  open: boolean;
  onClose: () => void;
}

const AssessmentSettingsModal = ({
  open,
  onClose,
}: AssessmentSettingsModalProps) => {
  const [form] = Form.useForm();
  const message = useMessage();
  const { handleError } = useAPIHelper();

  // State for tracking custom cron vs preset
  const [showCustomCron, setShowCustomCron] = useState(false);

  // API hooks
  const {
    data: config,
    isLoading: isLoadingConfig,
    refetch: refetchConfig,
  } = useGetAssessmentConfigQuery(undefined, { skip: !open });
  const { data: defaults } = useGetAssessmentConfigDefaultsQuery(undefined, {
    skip: !open,
  });

  // Track if we've initialized the form for this modal session
  const [formInitialized, setFormInitialized] = useState(false);

  // Refetch config and reset initialization state when modal opens/closes
  useEffect(() => {
    if (open) {
      refetchConfig();
      setFormInitialized(false);
    }
  }, [open, refetchConfig]);
  const {
    data: channelsData,
    isLoading: isLoadingChannels,
    refetch: refetchChannels,
  } = useGetChatChannelsQuery(undefined, { skip: !open });
  const [updateConfig, { isLoading: isUpdating }] =
    useUpdateAssessmentConfigMutation();
  const [testSlackChannel, { isLoading: isTesting }] =
    useTestSlackChannelMutation();

  // Watch form values for conditional rendering
  const reassessmentEnabled = Form.useWatch("reassessment_enabled", form);
  const slackChannelId = Form.useWatch("slack_channel_id", form);

  // Initialize form when config loads (only once per modal session)
  useEffect(() => {
    if (config && open && !formInitialized) {
      // Determine if current cron matches a preset
      const matchingPreset = FREQUENCY_OPTIONS.find(
        (opt) => opt.cron === config.reassessment_cron,
      );

      if (matchingPreset) {
        setShowCustomCron(false);
        form.setFieldsValue({
          assessment_model_override: config.assessment_model_override || "",
          chat_model_override: config.chat_model_override || "",
          reassessment_enabled: config.reassessment_enabled,
          frequency_preset: matchingPreset.value,
          reassessment_cron: config.reassessment_cron,
          slack_channel_id: config.slack_channel_id || undefined,
        });
      } else {
        setShowCustomCron(true);
        form.setFieldsValue({
          assessment_model_override: config.assessment_model_override || "",
          chat_model_override: config.chat_model_override || "",
          reassessment_enabled: config.reassessment_enabled,
          frequency_preset: "custom",
          reassessment_cron: config.reassessment_cron,
          slack_channel_id: config.slack_channel_id || undefined,
        });
      }
      setFormInitialized(true);
    }
  }, [config, form, open, formInitialized]);

  const handleFrequencyChange = (value: string) => {
    if (value === "custom") {
      setShowCustomCron(true);
    } else {
      setShowCustomCron(false);
      const preset = FREQUENCY_OPTIONS.find((opt) => opt.value === value);
      if (preset) {
        form.setFieldValue("reassessment_cron", preset.cron);
      }
    }
  };

  const handleTestChannel = async () => {
    const channelId = form.getFieldValue("slack_channel_id");
    if (!channelId) {
      message.warning("Please select a channel first");
      return;
    }

    const result = await testSlackChannel({ channel_id: channelId });
    if (isErrorResult(result)) {
      handleError(result.error);
    } else if (result.data) {
      if (result.data.success) {
        message.success(result.data.message);
      } else {
        message.error(result.data.message);
      }
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      // Find channel name for display
      const selectedChannel = channelsData?.channels.find(
        (ch) => ch.id === values.slack_channel_id,
      );

      const result = await updateConfig({
        assessment_model_override: values.assessment_model_override || null,
        chat_model_override: values.chat_model_override || null,
        reassessment_enabled: values.reassessment_enabled,
        reassessment_cron: values.reassessment_cron,
        slack_channel_id: values.slack_channel_id || null,
        slack_channel_name: selectedChannel?.name || null,
      });

      if (isErrorResult(result)) {
        handleError(result.error);
      } else {
        message.success("Assessment settings saved successfully");
        onClose();
      }
    } catch {
      // Form validation error - handled by antd
    }
  };

  const channelOptions =
    channelsData?.channels.map((ch) => ({
      label: `#${ch.name}`,
      value: ch.id,
    })) ?? [];

  return (
    <Modal
      title="Assessment Settings"
      open={open}
      onCancel={onClose}
      width={600}
      destroyOnClose
      footer={
        <Flex justify="flex-end" gap={8}>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="primary"
            onClick={handleSave}
            loading={isUpdating}
            disabled={isLoadingConfig}
          >
            Save
          </Button>
        </Flex>
      }
    >
      <Form form={form} layout="vertical" className="mt-4">
        {/* LLM Configuration Section */}
        <Flex vertical className="mb-6">
          <Text strong className="mb-3 block text-base">
            LLM Model Configuration
          </Text>

          <Form.Item
            name="assessment_model_override"
            label="Assessment Model Override"
            tooltip="Custom LLM model for running privacy assessments. Leave empty to use the default."
          >
            <Input
              placeholder={
                defaults?.default_assessment_model ||
                "openrouter/anthropic/claude-opus-4"
              }
              data-testid="input-assessment-model"
            />
          </Form.Item>

          <Form.Item
            name="chat_model_override"
            label="Chat Model Override"
            tooltip="Custom LLM model for questionnaire chat conversations. Leave empty to use the default."
          >
            <Input
              placeholder={
                defaults?.default_chat_model ||
                "openrouter/google/gemini-2.5-flash"
              }
              data-testid="input-chat-model"
            />
          </Form.Item>
        </Flex>

        {/* Re-assessment Schedule Section */}
        <Flex vertical className="mb-6">
          <Text strong className="mb-3 block text-base">
            Automatic Re-assessment
          </Text>

          <Form.Item
            name="reassessment_enabled"
            label="Enable Automatic Re-assessment"
            valuePropName="checked"
          >
            <Switch data-testid="switch-reassessment-enabled" />
          </Form.Item>

          {reassessmentEnabled && (
            <>
              <Form.Item
                name="frequency_preset"
                label="Schedule Frequency"
                initialValue="daily"
              >
                <Select
                  aria-label="Schedule Frequency"
                  options={[
                    ...FREQUENCY_OPTIONS,
                    { label: "Custom (Advanced)", value: "custom" },
                  ]}
                  onChange={handleFrequencyChange}
                  data-testid="select-frequency"
                />
              </Form.Item>

              {showCustomCron && (
                <Form.Item
                  name="reassessment_cron"
                  label="Cron Expression"
                  tooltip="Enter a valid cron expression (e.g., '0 9 * * *' for daily at 9am)"
                  rules={[
                    {
                      required: true,
                      message: "Please enter a cron expression",
                    },
                    {
                      validator: (_, value) => {
                        if (!value) {
                          return Promise.resolve();
                        }
                        if (parseCronExpression(value)) {
                          return Promise.resolve();
                        }
                        return Promise.reject(
                          new Error(
                            "Invalid cron expression. Use format: minute hour day month weekday (e.g., '0 9 * * *')",
                          ),
                        );
                      },
                    },
                  ]}
                >
                  <Input placeholder="0 9 * * *" data-testid="input-cron" />
                </Form.Item>
              )}

              {/* Hidden field to always have cron value */}
              {!showCustomCron && (
                <Form.Item name="reassessment_cron" hidden>
                  <Input />
                </Form.Item>
              )}
            </>
          )}
        </Flex>

        {/* Slack Configuration Section */}
        <Flex vertical className="mb-2">
          <Text strong className="mb-3 block text-base">
            Slack Notifications
          </Text>

          {channelOptions.length === 0 && !isLoadingChannels && (
            <Alert
              type="info"
              message="No Slack channels available"
              description="Please configure and authorize Slack in Settings > Notifications > Chat providers first."
              className="mb-4"
            />
          )}

          <Form.Item
            name="slack_channel_id"
            label="Questionnaire Notifications Channel"
            tooltip="Select the Slack channel where questionnaire notifications will be sent"
          >
            <Select
              aria-label="Questionnaire Notifications Channel"
              options={channelOptions}
              placeholder="Select a channel"
              loading={isLoadingChannels}
              disabled={channelOptions.length === 0}
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "")
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
              onDropdownVisibleChange={(visible) => {
                if (visible) {
                  refetchChannels();
                }
              }}
              data-testid="select-slack-channel"
            />
          </Form.Item>

          <Space>
            <Button
              onClick={handleTestChannel}
              loading={isTesting}
              disabled={!slackChannelId}
              data-testid="btn-test-channel"
            >
              Test Channel
            </Button>
          </Space>
        </Flex>
      </Form>
    </Modal>
  );
};

export default AssessmentSettingsModal;
