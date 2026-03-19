import {
  Button,
  Flex,
  Form,
  Select,
  Skeleton,
  Switch,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { POLL_INTERVAL_OPTIONS } from "./constants";
import {
  useCreateQueryLogConfigMutation,
  useDeleteQueryLogConfigMutation,
  useGetQueryLogConfigsQuery,
  useTestQueryLogConnectionMutation,
  useTriggerQueryLogPollMutation,
  useUpdateQueryLogConfigMutation,
} from "./query-log-config.slice";

interface FormValues {
  enabled: boolean;
  poll_interval_seconds: number;
}

const DEFAULT_VALUES: FormValues = {
  enabled: false,
  poll_interval_seconds: 300,
};

interface QueryLogConfigTabProps {
  integration: { key: string; name?: string };
}

const QueryLogConfigTab = ({ integration }: QueryLogConfigTabProps) => {
  const [form] = Form.useForm<FormValues>();
  const message = useMessage();

  const { data: configsResponse, isLoading: isLoadingConfigs } =
    useGetQueryLogConfigsQuery({
      connection_config_key: integration.key,
      page: 1,
      size: 1,
    });

  const existingConfig = useMemo(
    () => configsResponse?.items?.[0],
    [configsResponse],
  );

  const [createConfig, { isLoading: isCreating }] =
    useCreateQueryLogConfigMutation();
  const [updateConfig, { isLoading: isUpdating }] =
    useUpdateQueryLogConfigMutation();
  const [deleteConfig, { isLoading: isDeleting }] =
    useDeleteQueryLogConfigMutation();
  const [testConnection, { isLoading: isTesting }] =
    useTestQueryLogConnectionMutation();
  const [triggerPoll, { isLoading: isPolling }] =
    useTriggerQueryLogPollMutation();

  const isSaving = isCreating || isUpdating || isDeleting;

  const enabled = Form.useWatch("enabled", form);

  const initialValues: FormValues = useMemo(
    () => ({
      enabled: existingConfig?.enabled ?? DEFAULT_VALUES.enabled,
      poll_interval_seconds:
        existingConfig?.poll_interval_seconds ??
        DEFAULT_VALUES.poll_interval_seconds,
    }),
    [existingConfig],
  );

  const handleSubmit = useCallback(
    async (values: FormValues) => {
      try {
        if (values.enabled && !existingConfig) {
          // Create new config
          await createConfig({
            name: `${integration.name ?? integration.key} query log`,
            connection_config_key: integration.key,
            enabled: true,
            poll_interval_seconds: values.poll_interval_seconds,
          }).unwrap();
          message.success("Query logging enabled");
        } else if (values.enabled && existingConfig) {
          // Update existing config
          await updateConfig({
            configKey: existingConfig.key,
            enabled: true,
            poll_interval_seconds: values.poll_interval_seconds,
          }).unwrap();
          message.success("Query logging settings updated");
        } else if (!values.enabled && existingConfig) {
          // Disable — delete the config
          await deleteConfig(existingConfig.key).unwrap();
          message.success("Query logging disabled");
        }
      } catch (err) {
        message.error(getErrorMessage(err as RTKErrorResult["error"]));
      }
    },
    [
      existingConfig,
      integration,
      createConfig,
      updateConfig,
      deleteConfig,
      message,
    ],
  );

  const handleTest = useCallback(async () => {
    if (!existingConfig) {
      return;
    }
    try {
      const result = await testConnection(existingConfig.key).unwrap();
      if (result.success) {
        message.success(result.message);
      } else {
        message.error(result.message);
      }
    } catch (err) {
      message.error(
        getErrorMessage(
          err as RTKErrorResult["error"],
          "Connection test failed",
        ),
      );
    }
  }, [existingConfig, testConnection, message]);

  const handlePoll = useCallback(async () => {
    if (!existingConfig) {
      return;
    }
    try {
      const result = await triggerPoll(existingConfig.key).unwrap();
      message.success(`${result.entries_processed} entries processed`);
    } catch (err) {
      message.error(
        getErrorMessage(err as RTKErrorResult["error"], "Poll failed"),
      );
    }
  }, [existingConfig, triggerPoll, message]);

  return (
    <div className="max-w-[600px]">
      <Typography.Paragraph className="mb-4">
        Enable query logging to track and audit database queries for this
        integration.
      </Typography.Paragraph>

      {isLoadingConfigs ? (
        <Skeleton.Input active className="mt-4" />
      ) : (
        <Form
          form={form}
          layout="horizontal"
          onFinish={handleSubmit}
          initialValues={initialValues}
          requiredMark={false}
          key={existingConfig?.key ?? "new"}
        >
          <Form.Item
            name="enabled"
            label="Enable query logging"
            valuePropName="checked"
          >
            <Switch data-testid="query-log-enabled-switch" />
          </Form.Item>

          {enabled && (
            <Form.Item
              name="poll_interval_seconds"
              label="Poll interval"
              rules={[{ required: true, message: "Poll interval is required" }]}
            >
              <Select
                options={POLL_INTERVAL_OPTIONS}
                className="w-[200px]"
                aria-label="Poll interval"
                data-testid="query-log-poll-interval-select"
              />
            </Form.Item>
          )}

          <Form.Item>
            <Flex gap="small">
              <Button
                type="primary"
                htmlType="submit"
                loading={isSaving}
                data-testid="query-log-save-btn"
              >
                Save
              </Button>
              {enabled && existingConfig && (
                <>
                  <Button
                    onClick={handleTest}
                    loading={isTesting}
                    data-testid="query-log-test-btn"
                  >
                    Test connection
                  </Button>
                  <Button
                    onClick={handlePoll}
                    loading={isPolling}
                    data-testid="query-log-poll-btn"
                  >
                    Poll now
                  </Button>
                </>
              )}
            </Flex>
          </Form.Item>
        </Form>
      )}
    </div>
  );
};

export default QueryLogConfigTab;
