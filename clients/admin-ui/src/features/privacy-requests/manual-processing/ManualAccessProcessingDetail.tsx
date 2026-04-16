import {
  Button,
  Divider,
  Drawer,
  Flex,
  Form,
  Input,
  Typography,
} from "fidesui";
import { PatchUploadManualWebhookDataRequest } from "privacy-requests/types";
import React, { useState } from "react";

import { ManualProcessingDetailProps } from "./types";

const ManualAccessProcessingDetail = ({
  connectorName,
  data,
  isSubmitting = false,
  onSaveClick,
}: ManualProcessingDetailProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [form] = Form.useForm();

  const handleFinish = async (values: Record<string, string>) => {
    const params: PatchUploadManualWebhookDataRequest = {
      connection_key: data.connection_key,
      privacy_request_id: data.privacy_request_id,
      body: { ...values } as object,
    };
    onSaveClick(params);
    setIsOpen(false);
  };

  return (
    <>
      {data?.checked && (
        <Button onClick={() => setIsOpen(true)} size="small">
          Review
        </Button>
      )}
      {!data?.checked && (
        <Button onClick={() => setIsOpen(true)} size="small" type="primary">
          Begin manual input
        </Button>
      )}
      <Drawer
        open={isOpen}
        onClose={() => setIsOpen(false)}
        size="large"
        title={
          <>
            <Typography.Text className="mb-8 text-xl">
              {connectorName}
            </Typography.Text>
            <Divider />
            <Typography.Text className="mt-4 text-base">
              Manual access
            </Typography.Text>
            <div className="mt-2">
              <Typography.Text
                type="secondary"
                size="sm"
                className="font-normal"
              >
                Please complete the following PII fields that have been
                collected for the selected subject.
              </Typography.Text>
            </div>
          </>
        }
        footer={
          <Flex gap="small">
            <Button onClick={() => setIsOpen(false)}>Cancel</Button>
            <Button
              form="manual-detail-form"
              loading={isSubmitting}
              htmlType="submit"
            >
              Save
            </Button>
          </Flex>
        }
      >
        <Form
          form={form}
          id="manual-detail-form"
          initialValues={{ ...data.fields }}
          onFinish={handleFinish}
          key={JSON.stringify(data.fields)}
        >
          <Flex vertical gap="large">
            {Object.entries(data.fields).map(([key]) => (
              <Flex key={key} align="baseline">
                <Typography.Text strong size="sm" className="w-1/2">
                  {key}
                </Typography.Text>
                <Form.Item name={key} className="mb-0 flex-1">
                  <Input
                    autoComplete="off"
                    placeholder={`Please enter ${key}`}
                    size="small"
                  />
                </Form.Item>
              </Flex>
            ))}
          </Flex>
        </Form>
      </Drawer>
    </>
  );
};

export default ManualAccessProcessingDetail;
