import {
  Alert,
  Button,
  Divider,
  Flex,
  Form,
  Input,
  Modal,
  Select,
  Spin,
  Switch,
  Typography,
  useMessage,
} from "fidesui";
import NextLink from "next/link";
import { useEffect, useMemo } from "react";

import { useGetChatChannelsQuery } from "~/features/chat-provider/chatProvider.slice";
import { LlmModelOverrideField } from "~/features/common/form/LlmModelOverrideField";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import { parseCronExpression } from "~/features/digests/helpers/cronHelpers";

import { FREQUENCY_OPTIONS } from "./constants";
import {
  useGetAssessmentConfigDefaultsQuery,
  useGetAssessmentConfigQuery,
  useUpdateAssessmentConfigMutation,
} from "./privacy-assessments.slice";

const { Title } = Typography;

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

  // API hooks
  const {
    data: config,
    isLoading: isLoadingConfig,
    refetch: refetchConfig,
  } = useGetAssessmentConfigQuery(undefined, { skip: !open });
  const { data: defaults } = useGetAssessmentConfigDefaultsQuery(undefined, {
    skip: !open,
  });

  // Refetch config when modal opens
  useEffect(() => {
    if (open) {
      refetchConfig();
    }
  }, [open, refetchConfig]);

  const {
    data: channelsData,
    isLoading: isLoadingChannels,
    refetch: refetchChannels,
  } = useGetChatChannelsQuery(undefined, { skip: !open });
  const [updateConfig, { isLoading: isUpdating }] =
    useUpdateAssessmentConfigMutation();

  // Derive initial form values from config
  const initialValues = useMemo(() => {
    if (!config) {
      return undefined;
    }
    const matchingPreset = FREQUENCY_OPTIONS.find(
      (opt) => opt.cron === config.reassessment_cron,
    );
    return {
      assessment_model_override: config.assessment_model_override || "",
      chat_model_override: config.chat_model_override || "",
      reassessment_enabled: config.reassessment_enabled,
      frequency_preset: matchingPreset ? matchingPreset.value : "custom",
      reassessment_cron: config.reassessment_cron,
      slack_channel_id: config.slack_channel_id || undefined,
    };
  }, [config]);

  // Watch form values for conditional rendering
  const reassessmentEnabled = Form.useWatch("reassessment_enabled", form);
  const frequencyPreset = Form.useWatch("frequency_preset", form);
  const showCustomCron = frequencyPreset === "custom";

  const handleFrequencyChange = (value: string) => {
    if (value !== "custom") {
      const preset = FREQUENCY_OPTIONS.find((opt) => opt.value === value);
      if (preset) {
        form.setFieldValue("reassessment_cron", preset.cron);
      }
    }
  };

  const handleSave = async () => {
    const values = await form.validateFields();

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
      message.error(getErrorMessage(result.error));
    } else {
      message.success("Assessment settings saved successfully");
      onClose();
    }
  };

  const channelOptions =
    channelsData?.channels.map((ch) => ({
      label: `#${ch.name}`,
      value: ch.id,
    })) ?? [];

  return (
    <Modal
      title="Assessment settings"
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
            disabled={isLoadingConfig || !config}
          >
            Save
          </Button>
        </Flex>
      }
    >
      {isLoadingConfig || !config ? (
        <Flex justify="center" className="py-8">
          <Spin />
        </Flex>
      ) : (
        <Form form={form} layout="horizontal" initialValues={initialValues}>
          {/* LLM Configuration Section */}
          <Flex vertical>
            <div className="mb-3">
              <Title level={5}>LLM model configuration</Title>
            </div>

            <LlmModelOverrideField
              name="assessment_model_override"
              label="Assessment model"
              tooltip="Custom LLM model for running privacy assessments. Leave empty to use the default."
              placeholder={defaults?.default_assessment_model}
              testId="assessment-model"
            />

            <LlmModelOverrideField
              name="chat_model_override"
              label="Chat model"
              tooltip="Custom LLM model for questionnaire chat conversations. Leave empty to use the default."
              placeholder={defaults?.default_chat_model}
              testId="chat-model"
            />
          </Flex>

          <Divider className="mt-2" />

          {/* Re-assessment Schedule Section */}
          <Flex vertical>
            <div className="mb-3">
              <Title level={5}>Automatic reassessment</Title>
            </div>

            <Form.Item
              name="reassessment_enabled"
              label="Enable automatic reassessment"
              valuePropName="checked"
            >
              <Switch data-testid="switch-reassessment-enabled" />
            </Form.Item>

            {reassessmentEnabled && (
              <>
                <Form.Item name="frequency_preset" label="Schedule frequency">
                  <Select
                    aria-label="Schedule frequency"
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
                    label="Cron expression"
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

          <Divider className="mt-2" />

          {/* Slack Configuration Section */}
          <Flex vertical>
            <div className="mb-3">
              <Title level={5}>Slack notifications</Title>
            </div>

            {channelOptions.length === 0 && !isLoadingChannels ? (
              <Alert
                type="info"
                message="Configure Slack to enable channel notifications."
                action={
                  <NextLink
                    href={CHAT_PROVIDERS_ROUTE}
                    target="_blank"
                    passHref
                  >
                    <Button size="small" type="link">
                      Configure Slack
                    </Button>
                  </NextLink>
                }
                className="mb-4"
              />
            ) : (
              <Form.Item
                name="slack_channel_id"
                label="Questionnaire notifications channel"
                tooltip="Select the Slack channel where questionnaire notifications will be sent"
              >
                <Select
                  aria-label="Questionnaire notifications channel"
                  options={channelOptions}
                  placeholder="Select a channel"
                  loading={isLoadingChannels}
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
            )}
          </Flex>
        </Form>
      )}
    </Modal>
  );
};

export default AssessmentSettingsModal;
