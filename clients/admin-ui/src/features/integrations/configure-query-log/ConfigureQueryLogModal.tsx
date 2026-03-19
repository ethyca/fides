import {
  Flex,
  Input,
  Modal,
  Select,
  Switch,
  Typography,
  useMessage,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import { useCallback } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  POLL_INTERVAL_OPTIONS,
  PollInterval,
} from "~/features/integrations/configure-query-log/constants";
import {
  type CreateQueryLogConfigRequest,
  type QueryLogConfigResponse,
  useCreateQueryLogConfigMutation,
  useUpdateQueryLogConfigMutation,
} from "~/features/integrations/configure-query-log/query-log-config.slice";
import { RTKErrorResult } from "~/types/errors/api";

interface ConfigureQueryLogModalProps {
  isOpen: boolean;
  onClose: () => void;
  config?: QueryLogConfigResponse;
  isEditing: boolean;
  integrationKey: string;
}

interface FormValues {
  name: string;
  key: string;
  enabled: boolean;
  poll_interval_seconds: number;
}

const generateKey = (name: string): string =>
  name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");

const ConfigureQueryLogModal = ({
  isOpen,
  onClose,
  config,
  isEditing,
  integrationKey,
}: ConfigureQueryLogModalProps) => {
  const message = useMessage();
  const [createQueryLogConfig] = useCreateQueryLogConfigMutation();
  const [updateQueryLogConfig] = useUpdateQueryLogConfigMutation();

  const initialValues: FormValues = {
    name: config?.name ?? "",
    key: config?.key ?? "",
    enabled: config?.enabled ?? true,
    poll_interval_seconds:
      config?.poll_interval_seconds ?? PollInterval.FIVE_MINUTES,
  };

  const handleSubmit = useCallback(
    async (values: FormValues, helpers: FormikHelpers<FormValues>) => {
      try {
        if (isEditing && config) {
          await updateQueryLogConfig({
            configKey: config.key,
            name: values.name,
            enabled: values.enabled,
            poll_interval_seconds: values.poll_interval_seconds,
          }).unwrap();
          message.success("Query log config updated successfully");
        } else {
          const body: CreateQueryLogConfigRequest = {
            connection_config_key: integrationKey,
            name: values.name,
            key: values.key,
            enabled: values.enabled,
            poll_interval_seconds: values.poll_interval_seconds,
          };
          await createQueryLogConfig(body).unwrap();
          message.success("Query log config created successfully");
        }
        onClose();
      } catch (error) {
        message.error(
          getErrorMessage(
            error as RTKErrorResult["error"],
            "An error occurred saving the query log config.",
          ),
        );
      } finally {
        helpers.setSubmitting(false);
      }
    },
    [
      isEditing,
      config,
      integrationKey,
      createQueryLogConfig,
      updateQueryLogConfig,
      message,
      onClose,
    ],
  );

  return (
    <Modal
      title={
        isEditing ? `Edit ${config?.name ?? "config"}` : "Add query log config"
      }
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnClose
      footer={null}
      data-testid="query-log-config-modal"
    >
      <Formik<FormValues>
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
      >
        {({ values, setFieldValue, isSubmitting, submitForm }) => (
          <Form>
            <Flex vertical gap={16} className="py-4">
              <div>
                <Typography.Text strong className="mb-1 block">
                  Name
                </Typography.Text>
                <Input
                  value={values.name}
                  onChange={(e) => {
                    const newName = e.target.value;
                    setFieldValue("name", newName);
                    if (!isEditing) {
                      setFieldValue("key", generateKey(newName));
                    }
                  }}
                  placeholder="Enter config name"
                  data-testid="query-log-config-name-input"
                />
              </div>

              <div>
                <Typography.Text strong className="mb-1 block">
                  Key
                </Typography.Text>
                <Input
                  value={values.key}
                  disabled={isEditing}
                  onChange={(e) => setFieldValue("key", e.target.value)}
                  placeholder="Auto-generated from name"
                  data-testid="query-log-config-key-input"
                />
              </div>

              <Flex align="center" gap={8}>
                <Switch
                  checked={values.enabled}
                  onChange={(checked) => setFieldValue("enabled", checked)}
                  aria-label="Enabled"
                  data-testid="query-log-config-enabled-switch"
                />
                <Typography.Text>
                  {values.enabled ? "Enabled" : "Disabled"}
                </Typography.Text>
              </Flex>

              <div>
                <Typography.Text strong className="mb-1 block">
                  Poll interval
                </Typography.Text>
                <Select
                  value={values.poll_interval_seconds}
                  onChange={(value) =>
                    setFieldValue("poll_interval_seconds", value)
                  }
                  options={POLL_INTERVAL_OPTIONS}
                  aria-label="Poll interval"
                  className="w-full"
                  data-testid="query-log-config-poll-select"
                />
              </div>

              <Flex justify="flex-end" gap={8} className="mt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="ant-btn ant-btn-default"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={submitForm}
                  disabled={isSubmitting || !values.name}
                  className="ant-btn ant-btn-primary"
                >
                  {isEditing ? "Update" : "Create"}
                </button>
              </Flex>
            </Flex>
          </Form>
        )}
      </Formik>
    </Modal>
  );
};

export default ConfigureQueryLogModal;
