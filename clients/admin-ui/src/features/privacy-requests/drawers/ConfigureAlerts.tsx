import {
  Button,
  Divider,
  Drawer,
  Flex,
  Form,
  Icons,
  InputNumber,
  Space,
  Typography,
  Switch,
} from "fidesui";
import { useEffect, useRef, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { InfoTooltip } from "~/features/common/InfoTooltip";

import EmailChipList from "../EmailChipList";
import {
  useGetNotificationQuery,
  useSaveNotificationMutation,
} from "../privacy-requests.slice";

const DEFAULT_MIN_ERROR_COUNT = 1;

const ConfigureAlerts = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [emails, setEmails] = useState<string[]>([]);
  const [notify, setNotify] = useState(true);
  const [minErrorCount, setMinErrorCount] = useState(DEFAULT_MIN_ERROR_COUNT);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const firstField = useRef(null);
  const { errorAlert, successAlert } = useAlert();
  const [skip, setSkip] = useState(true);

  const { data } = useGetNotificationQuery(undefined, { skip });
  const [saveNotification] = useSaveNotificationMutation();

  const handleSubmit = async () => {
    setIsSubmitting(true);
    const payload = await saveNotification({
      email_addresses: notify ? emails : [],
      notify_after_failures: notify ? minErrorCount : 0,
    });
    if (isErrorResult(payload)) {
      errorAlert(
        getErrorMessage(payload.error),
        "Failed to save notification settings",
      );
    } else {
      successAlert("Notification settings saved successfully");
    }
    setIsSubmitting(false);
    setIsOpen(false);
  };

  const handleClose = () => {
    setIsOpen(false);
    // Reset form to defaults when drawer closes
    setEmails([]);
    setNotify(true);
    setMinErrorCount(DEFAULT_MIN_ERROR_COUNT);
  };

  useEffect(() => {
    if (isOpen) {
      setSkip(false);
    }
  }, [isOpen]);

  useEffect(() => {
    if (data) {
      // Only populate from API data, never use dummy/pre-seeded emails
      // Ensure we always use an array, even if API returns undefined/null
      setEmails(
        Array.isArray(data.email_addresses) ? data.email_addresses : [],
      );
      setNotify(data.notify_after_failures !== 0);
      setMinErrorCount(data.notify_after_failures ?? DEFAULT_MIN_ERROR_COUNT);
    }
    // If no data exists, state remains at initial defaults (empty emails array)
  }, [data]);

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        title="Configure alerts"
        aria-label="Configure alerts"
        icon={<Icons.Notification />}
      />
      <Drawer
        open={isOpen}
        onClose={handleClose}
        placement="right"
        width={480}
        title="Request notifications"
        footer={
          <Flex gap="small" justify="flex-end">
            <Button onClick={handleClose}>Cancel</Button>
            <Button
              type="primary"
              onClick={handleSubmit}
              loading={isSubmitting}
            >
              Save
            </Button>
          </Flex>
        }
      >
        <Form layout="vertical" onFinish={handleSubmit}>
          <Typography.Text type="secondary">
            Get notified when processing failures occur. Set a threshold to
            receive alerts after a specific number of errors.
          </Typography.Text>
          <Space direction="vertical" size="middle" className="w-full">
            <Form.Item className="mb-0">
              <Flex
                justify="space-between"
                align="center"
              >
                <label htmlFor="enable-email-notifications">
                  Enable email notifications
                </label>
                <Switch
                  id="enable-email-notifications"
                  size="small"
                  checked={notify}
                  onChange={(checked) => {
                    setNotify(checked);
                    if (!checked) {
                      setMinErrorCount(DEFAULT_MIN_ERROR_COUNT);
                    }
                  }}
                />
              </Flex>
            </Form.Item>

            <Divider style={{ margin: "8px 0 12px 0" }} />

            <Form.Item
              label={
                <Flex align="center" gap={4}>
                  <span>Email addresses</span>
                  <InfoTooltip label="Type or paste email addresses separated by commas and press Enter or Tab to add them" />
                </Flex>
              }
            >
              <EmailChipList
                emails={emails}
                onEmailsChange={setEmails}
                ref={firstField}
                disabled={!notify}
              />
            </Form.Item>

            {notify && (
              <>
                <Divider className="mt-2 mb-3" />
                <Form.Item
                  label="Notification frequency"
                  help="You'll receive an email when the number of unsent errors reaches this threshold. Set to 1 for immediate alerts, or increase to batch notifications."
                >
                  <Flex align="center" gap="small">
                    <span>Send notification after</span>
                    <InputNumber
                      min={DEFAULT_MIN_ERROR_COUNT}
                      value={minErrorCount}
                      onChange={(value) =>
                        setMinErrorCount(value ?? DEFAULT_MIN_ERROR_COUNT)
                      }
                      className="w-20"
                    />
                    <span>error(s)</span>
                  </Flex>
                </Form.Item>
              </>
            )}
          </Space>
        </Form>
      </Drawer>
    </>
  );
};

export default ConfigureAlerts;
