import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { Button, Form, Input, Spin, useMessage } from "fidesui";
import { useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useUpdateOrganizationMutation,
} from "~/features/organization";
import { Organization } from "~/types/api";

// NOTE: This form only supports *editing* Organizations right now, and
// does not support creation/deletion. Since Fides will automatically create the
// "default_organization" on startup, this works!
//
// However, note that if the provided `organization` prop is null, the form
// will still render but all fields will be disabled and it will display as
// "loading". This allows the form to render immediately while the parent
// fetches the Organization via the API
interface OrganizationFormProps {
  organization?: Organization;
  isLoading?: boolean;
  onSuccess?: (organization: Organization) => void;
}

export interface OrganizationFormValues extends Organization {}

export const defaultInitialValues: OrganizationFormValues = {
  description: "",
  fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
  name: "",
};

// NOTE: These transform functions are (basically) unnecessary right now, since
// the form values are an exact match to the Organization object. However, in
// future iterations some transformation is likely to be necessary, so we've
// put these transform functions in place ahead of time to make future updates
// easier to make
export const transformOrganizationToFormValues = (
  organization: Organization,
): OrganizationFormValues => ({ ...organization });

export const transformFormValuesToOrganization = (
  formValues: OrganizationFormValues,
): Organization => ({
  description: formValues.description,
  fides_key: formValues.fides_key,
  name: formValues.name,
});

export const OrganizationForm = ({
  organization,
  isLoading,
  onSuccess,
}: OrganizationFormProps) => {
  const [form] = Form.useForm<OrganizationFormValues>();
  const [updateOrganizationMutation] = useUpdateOrganizationMutation();
  const [isDirty, setIsDirty] = useState(false);
  const message = useMessage();

  const initialValues = useMemo(
    () =>
      organization
        ? transformOrganizationToFormValues(organization)
        : defaultInitialValues,
    [organization],
  );

  const handleSubmit = async (values: OrganizationFormValues) => {
    const organizationBody = transformFormValuesToOrganization(values);

    const handleResult = (
      result:
        | { data: object }
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
        setIsDirty(false);
        if (onSuccess) {
          onSuccess(organizationBody);
        }
      }
    };

    const result = await updateOrganizationMutation(organizationBody);
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
      onValuesChange={() => setIsDirty(true)}
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
          disabled={isLoading || !isDirty}
          loading={isLoading}
          data-testid="save-btn"
        >
          Save
        </Button>
      </div>
    </Form>
  );
};
