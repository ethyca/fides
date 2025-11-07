import {
  AntButton as Button,
  AntForm as Form,
  AntInputNumber as InputNumber,
  AntSwitch as Switch,
  AntTypography as Typography,
} from "fidesui";
import { useEffect } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  selectDuplicateDetectionSettings,
  useGetConfigurationSettingsQuery,
  usePatchConfigurationSettingsMutation,
} from "~/features/config-settings/config-settings.slice";
import { DuplicateDetectionApplicationConfig } from "~/types/api/models/DuplicateDetectionApplicationConfig";
import { isErrorResult } from "~/types/errors";

interface FormValues {
  enabled: boolean;
  time_window_days: number;
}

const PrivacyRequestDuplicateDetectionSettings = () => {
  const [form] = Form.useForm<FormValues>();
  const { errorAlert, successAlert } = useAlert();

  // Fetch current configuration
  const { isLoading } = useGetConfigurationSettingsQuery({ api_set: true });
  const duplicateDetectionSettings = useAppSelector(
    selectDuplicateDetectionSettings,
  );

  const [patchConfigurationSettings, { isLoading: isPatching }] =
    usePatchConfigurationSettingsMutation();

  // Watch the enabled field to conditionally show/hide time_window_days
  const enabled = Form.useWatch("enabled", form);

  // Update form when settings are loaded
  useEffect(() => {
    if (duplicateDetectionSettings) {
      form.setFieldsValue({
        enabled: duplicateDetectionSettings.enabled ?? false,
        time_window_days: duplicateDetectionSettings.time_window_days ?? 365,
      });
    }
  }, [duplicateDetectionSettings, form]);

  const handleSubmit = async (values: FormValues) => {
    const payload: {
      privacy_request_duplicate_detection: DuplicateDetectionApplicationConfig;
    } = {
      privacy_request_duplicate_detection: {
        enabled: values.enabled,
        time_window_days: values.time_window_days,
      },
    };

    const result = await patchConfigurationSettings(payload);
    if (isErrorResult(result)) {
      errorAlert(
        "An error occurred while updating duplicate detection settings.",
        getErrorMessage(result.error),
      );
    } else {
      successAlert("Duplicate detection settings updated successfully.");
    }
  };

  return (
    <div className="max-w-[600px]">
      <Typography.Title level={2} className="!mb-2">
        Duplicate detection
      </Typography.Title>
      <Typography.Paragraph>
        If you enable duplicate detection, Fides will automatically detect and
        label likely duplicate privacy requests. Any request submitted by the
        same email address within the configured period of time is automatically
        labeled with the status of &quot;duplicate&quot;.
      </Typography.Paragraph>

      <Form
        form={form}
        layout="horizontal"
        onFinish={handleSubmit}
        initialValues={{
          enabled: false,
          time_window_days: 365,
        }}
        className="mt-4"
      >
        <Form.Item
          name="enabled"
          label="Enable duplicate detection"
          valuePropName="checked"
        >
          <Switch data-testid="input-enabled" />
        </Form.Item>

        {enabled && (
          <Form.Item
            name="time_window_days"
            label="Duplicate detection window (days)"
            rules={[
              { required: true, message: "Required" },
              {
                type: "number",
                min: 1,
                max: 3650,
                message: "Must be between 1 and 3650 days",
              },
            ]}
          >
            <InputNumber
              min={1}
              max={3650}
              className="w-[200px]"
              data-testid="input-time_window_days"
            />
          </Form.Item>
        )}

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={isPatching}
            disabled={isLoading}
          >
            Save
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default PrivacyRequestDuplicateDetectionSettings;
