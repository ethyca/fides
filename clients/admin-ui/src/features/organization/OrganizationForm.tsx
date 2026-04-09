import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { Button, Form, Input, Spin, useMessage } from "fidesui";
import { useMemo } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useUpdateOrganizationMutation,
} from "~/features/organization";
import { Organization } from "~/types/api";

interface OrganizationFormProps {
  organization?: Organization;
  isLoading?: boolean;
  onSuccess?: (organization: Organization) => void;
}

const defaultInitialValues: Organization = {
  description: "",
  fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
  name: "",
};

export const OrganizationForm = ({
  organization,
  isLoading,
  onSuccess,
}: OrganizationFormProps) => {
  const [form] = Form.useForm<Organization>();
  const [updateOrganizationMutation] = useUpdateOrganizationMutation();
  const message = useMessage();

  const initialValues = useMemo(
    () => organization ?? defaultInitialValues,
    [organization],
  );

  const handleSubmit = async (values: Organization) => {
    const handleResult = (
      result:
        | { data: Organization }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the organization. Please try again.",
        );
        message.error(errorMsg);
      } else {
        message.success("Organization configuration saved.");
        const { fides_key: key, name, description } = result.data;
        form.setFieldsValue({ fides_key: key, name, description });
        if (onSuccess) {
          onSuccess(result.data);
        }
      }
    };

    const result = await updateOrganizationMutation(values);
    handleResult(result);
  };

  if (isLoading) {
    return <Spin />;
  }

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={handleSubmit}
      data-testid="organization-form"
    >
      <Form.Item
        name="fides_key"
        label="Fides key"
        tooltip="A unique key that identifies your organization. Not editable via UI."
      >
        <Input disabled data-testid="input-fides_key" />
      </Form.Item>
      <Form.Item
        name="name"
        label="Name"
        tooltip="User-friendly name for your organization, used in messaging to end-users and other public locations."
        rules={[{ required: true, message: "Name is required" }]}
      >
        <Input disabled={isLoading} data-testid="input-name" />
      </Form.Item>
      <Form.Item
        name="description"
        label="Description"
        tooltip="Short description of your organization, your services, etc."
        rules={[{ required: true, message: "Description is required" }]}
      >
        <Input disabled={isLoading} data-testid="input-description" />
      </Form.Item>
      <div className="text-right">
        <Button
          htmlType="submit"
          type="primary"
          disabled={isLoading}
          loading={isLoading}
          data-testid="save-btn"
        >
          Save
        </Button>
      </div>
    </Form>
  );
};
