import {
  Button,
  ChakraBellIcon as BellIcon,
  ChakraText as Text,
  Drawer,
  Flex,
  Form,
  InputNumber,
  Space,
  Switch,
} from "fidesui";
import { useEffect, useRef, useState } from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";

import EmailChipList from "../EmailChipList";
import {
  useGetNotificationQuery,
  useSaveNotificationMutation,
} from "../privacy-requests.slice";

const DEFAULT_MIN_ERROR_COUNT = 1;

const ConfigureAlerts = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [emails, setEmails] = useState<string[]>([]);
  const [notify, setNotify] = useState(false);
  const [minErrorCount, setMinErrorCount] = useState(DEFAULT_MIN_ERROR_COUNT);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const firstField = useRef(null);
  const { errorAlert, successAlert } = useAlert();
  const [skip, setSkip] = useState(true);

  const { data } = useGetNotificationQuery(undefined, { skip });
  const [saveNotification] = useSaveNotificationMutation();

  const handleSubmit = async () => {
    if (notify && emails.length === 0) {
      errorAlert("Please enter at least one email address");
      return;
    }

    setIsSubmitting(true);
    const payload = await saveNotification({
      email_addresses: emails,
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
  };

  useEffect(() => {
    if (isOpen) {
      setSkip(false);
    }
    if (data) {
      setEmails(data.email_addresses);
      setNotify(data.notify_after_failures !== 0);
      setMinErrorCount(data.notify_after_failures || DEFAULT_MIN_ERROR_COUNT);
    }
  }, [data, isOpen]);

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        title="Configure alerts"
        aria-label="Configure alerts"
        icon={<BellIcon />}
      />
      <Drawer
        open={isOpen}
        onClose={handleClose}
        placement="right"
        width={480}
        title="DSR notifications"
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
          <Text fontSize="sm" color="gray.600" mb={4}>
            Get notified when processing failures occur. Set a threshold to receive alerts after a specific number of errors.
          </Text>
          <Space direction="vertical" size="middle" className="w-full">
            <Form.Item
              label={
                <Flex align="center">
                  <span>Enter email</span>
                  <InfoTooltip label="Type or paste email addresses separated by commas and press Enter or Tab to add them" className="ml-1" />
                </Flex>
              }
              required={notify}
              validateStatus={notify && emails.length === 0 ? "error" : undefined}
              help={notify && emails.length === 0 ? "At least one email is required" : undefined}
            >
                          <EmailChipList
                emails={emails}
                onEmailsChange={setEmails}
                            ref={firstField}
                          />
            </Form.Item>

            <div>
              <Flex justify="space-between" align="center" className="w-full">
                <span>Notify on every error</span>
                            <Switch
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
              {notify && (
                <Flex align="center" gap={0} className="mt-2">
                  <span>Notify after</span>
                  <InputNumber
                    min={DEFAULT_MIN_ERROR_COUNT}
                    value={minErrorCount}
                    onChange={(value) => setMinErrorCount(value || DEFAULT_MIN_ERROR_COUNT)}
                    style={{ width: 80, marginLeft: 8, marginRight: 8 }}
                  />
                  <span>errors</span>
                </Flex>
              )}
            </div>
          </Space>
        </Form>
      </Drawer>
    </>
  );
};

export default ConfigureAlerts;
