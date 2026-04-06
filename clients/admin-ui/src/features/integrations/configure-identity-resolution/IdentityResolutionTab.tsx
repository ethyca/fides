import {
  Button,
  Flex,
  Form,
  Skeleton,
  Switch,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import {
  useCreateIdentityGroupProviderMutation,
  useGetIdentityGroupProvidersQuery,
  useTestIdentityGroupProviderMutation,
  useUpdateIdentityGroupProviderMutation,
} from "./identity-group-provider.slice";

interface FormValues {
  enabled: boolean;
}

const DEFAULT_VALUES: FormValues = {
  enabled: false,
};

interface IdentityResolutionTabProps {
  integration: { key: string; name?: string; connection_type?: string };
}

const IdentityResolutionTab = ({ integration }: IdentityResolutionTabProps) => {
  const [form] = Form.useForm<FormValues>();
  const message = useMessage();

  const { data: providersResponse, isLoading: isLoadingProviders } =
    useGetIdentityGroupProvidersQuery({
      connection_config_key: integration.key,
    });

  const existingProvider = useMemo(
    () => providersResponse?.items?.[0],
    [providersResponse],
  );

  const [createProvider, { isLoading: isCreating }] =
    useCreateIdentityGroupProviderMutation();
  const [updateProvider, { isLoading: isUpdating }] =
    useUpdateIdentityGroupProviderMutation();
  const [testProvider, { isLoading: isTesting }] =
    useTestIdentityGroupProviderMutation();

  const isSaving = isCreating || isUpdating;
  const enabled = Form.useWatch("enabled", form);

  // Infer provider type from connection type
  const providerType = useMemo(() => {
    if (integration.connection_type === "google_workspace") {
      return "google_workspace";
    }
    if (integration.connection_type === "test_datastore") {
      return "mock";
    }
    return "gcp";
  }, [integration.connection_type]);

  const initialValues: FormValues = useMemo(
    () => ({
      enabled: existingProvider?.enabled ?? DEFAULT_VALUES.enabled,
    }),
    [existingProvider],
  );

  const handleSubmit = useCallback(
    async (values: FormValues) => {
      try {
        if (values.enabled && !existingProvider) {
          await createProvider({
            name: `${integration.name ?? integration.key} identity resolution`,
            key: `${integration.key}-identity`,
            provider_type: providerType,
            connection_config_key: integration.key,
            enabled: true,
          }).unwrap();
          message.success("Identity resolution enabled");
        } else if (values.enabled && existingProvider) {
          await updateProvider({
            id: existingProvider.id,
            enabled: true,
          }).unwrap();
          message.success("Identity resolution settings updated");
        } else if (!values.enabled && existingProvider) {
          await updateProvider({
            id: existingProvider.id,
            enabled: false,
          }).unwrap();
          message.success("Identity resolution disabled");
        }
      } catch (err) {
        message.error(getErrorMessage(err as RTKErrorResult["error"]));
      }
    },
    [
      existingProvider,
      integration,
      providerType,
      createProvider,
      updateProvider,
      message,
    ],
  );

  const handleTest = useCallback(async () => {
    if (!existingProvider) {
      return;
    }
    try {
      const result = await testProvider(existingProvider.id).unwrap();
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
  }, [existingProvider, testProvider, message]);

  return (
    <div className="max-w-[600px]">
      <Typography.Paragraph className="mb-4">
        Enable identity resolution to map query authors to data consumers
        {providerType === "google_workspace" &&
          " using Google Groups membership"}
        {providerType === "gcp" &&
          " using GCP IAM role bindings and service account matching"}
        {providerType === "mock" &&
          " using mock data (no real credentials needed)"}
        .
      </Typography.Paragraph>

      {isLoadingProviders ? (
        <Skeleton.Input active className="mt-4" />
      ) : (
        <Form
          form={form}
          layout="horizontal"
          onFinish={handleSubmit}
          initialValues={initialValues}
          requiredMark={false}
          key={existingProvider?.id ?? "new"}
        >
          <Form.Item
            name="enabled"
            label="Enable identity resolution"
            valuePropName="checked"
          >
            <Switch data-testid="identity-resolution-enabled-switch" />
          </Form.Item>

          <Form.Item>
            <Flex gap="small">
              <Button
                type="primary"
                htmlType="submit"
                loading={isSaving}
                data-testid="identity-resolution-save-btn"
              >
                Save
              </Button>
              {enabled && existingProvider && (
                <Button
                  onClick={handleTest}
                  loading={isTesting}
                  data-testid="identity-resolution-test-btn"
                >
                  Test connection
                </Button>
              )}
            </Flex>
          </Form.Item>
        </Form>
      )}
    </div>
  );
};

export default IdentityResolutionTab;
