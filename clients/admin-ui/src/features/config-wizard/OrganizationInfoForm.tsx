import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useCreateOrganizationMutation,
  useGetOrganizationByFidesKeyQuery,
  useUpdateOrganizationMutation,
} from "~/features/organization";
import { Organization } from "~/types/api";
import { RTKErrorResult } from "~/types/errors/api";

import { changeStep, setOrganization } from "./config-wizard.slice";

interface FormValues {
  name: string;
  description: string;
}

export const OrganizationInfoForm = () => {
  const dispatch = useAppDispatch();
  const message = useMessage();
  const [form] = Form.useForm<FormValues>();
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const [createOrganization] = useCreateOrganizationMutation();
  const [updateOrganization] = useUpdateOrganizationMutation();
  const { data: existingOrg, isLoading: isLoadingOrganization } =
    useGetOrganizationByFidesKeyQuery(DEFAULT_ORGANIZATION_FIDES_KEY);

  // Track submittable state
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  // Auto-skip step if org already has name+description
  useEffect(() => {
    if (isLoadingOrganization || hasSubmitted) {
      return;
    }
    if (existingOrg?.name && existingOrg?.description) {
      dispatch(changeStep());
    }
  }, [isLoadingOrganization, existingOrg, dispatch, hasSubmitted]);

  const formInitialValues = useMemo(
    () => ({
      name: existingOrg?.name ?? "",
      description: existingOrg?.description ?? "",
    }),
    [existingOrg],
  );

  const handleSuccess = (organization: Organization) => {
    dispatch(setOrganization(organization));
    dispatch(changeStep());
  };

  const onFinish = async (values: FormValues) => {
    setHasSubmitted(true);
    const organizationBody = {
      name: values.name ?? existingOrg?.name,
      description: values.description ?? existingOrg?.description,
      fides_key: existingOrg?.fides_key ?? DEFAULT_ORGANIZATION_FIDES_KEY,
      organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
    };

    try {
      if (!existingOrg) {
        await createOrganization(organizationBody).unwrap();
      } else {
        await updateOrganization(organizationBody).unwrap();
      }
      handleSuccess(organizationBody);
    } catch (error) {
      const errorMsg = getErrorMessage(error as RTKErrorResult["error"]);
      message.error(errorMsg);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={formInitialValues}
      key={existingOrg?.fides_key ?? "create"}
      className="w-full max-w-xl"
      data-testid="organization-info-form"
    >
      <Flex vertical gap="large">
        <Typography.Title level={3}>Create your Organization</Typography.Title>
        <Card>
          <Flex vertical gap="middle">
            <div>
              Provide your organization information. This information is used to
              configure your organization in Fides for data map reporting
              purposes.
            </div>
            <Form.Item
              name="name"
              label="Organization name"
              tooltip="The legal name of your organization"
              rules={[
                { required: true, message: "Organization name is required" },
              ]}
            >
              <Input data-testid="input-name" />
            </Form.Item>
            <Form.Item
              name="description"
              label="Description"
              tooltip='An explanation of the type of organization and primary activity. For example "Acme Inc. is an e-commerce company that sells scarves."'
              rules={[
                {
                  required: true,
                  message: "Organization description is required",
                },
              ]}
            >
              <Input data-testid="input-description" />
            </Form.Item>
          </Flex>
        </Card>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            disabled={!submittable}
            data-testid="submit-btn"
          >
            Save and continue
          </Button>
        </Flex>
      </Flex>
    </Form>
  );
};
