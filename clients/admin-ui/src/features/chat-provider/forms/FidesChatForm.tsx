import {
  Alert,
  Button,
  Flex,
  Icons,
  Space,
  Typography,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";

import {
  useCreateChatConfigMutation,
  useGetChatConfigQuery,
} from "../chatProvider.slice";
import AuthorizationStatus from "../components/AuthorizationStatus";
import ConfigurationCard from "../components/ConfigurationCard";

const { Text } = Typography;

interface FidesChatFormProps {
  configId?: string;
}

const FidesChatForm = ({ configId }: FidesChatFormProps) => {
  const router = useRouter();
  const { handleError } = useAPIHelper();
  const message = useMessage();

  const { data: existingConfig } = useGetChatConfigQuery(configId!, {
    skip: !configId,
  });
  const [createConfig] = useCreateChatConfigMutation();

  const isEditMode = !!configId;
  const isAuthorized = !!existingConfig?.authorized;

  const handleCreate = async () => {
    try {
      const payload = {
        provider_type: "fides" as const,
      };

      const result = await createConfig(payload);

      if (isErrorResult(result)) {
        handleError(result.error);
      } else if ("data" in result && result.data) {
        message.success("Fides chat provider enabled.");
        router.push(`${CHAT_PROVIDERS_ROUTE}/configure?id=${result.data.id}`);
      }
    } catch (error) {
      handleError(error);
    }
  };

  return (
    <ConfigurationCard title="Fides chat provider" icon={<Icons.Checkmark />}>
      <Space orientation="vertical" size="medium" className="w-full">
        <Alert
          type="info"
          showIcon
          description={
            <Text>
              Use this provider to test the questionnaire feature directly in
              the Admin UI without configuring an external chat provider like
              Slack. Intended for testing and development only, not production
              usage.
            </Text>
          }
          title="How it works"
        />
        {isEditMode && isAuthorized && <AuthorizationStatus authorized />}
      </Space>

      {!isEditMode && (
        <Flex justify="flex-end" className="mt-6">
          <Space>
            <RouterLink href={CHAT_PROVIDERS_ROUTE}>
              <Button data-testid="cancel-btn">Cancel</Button>
            </RouterLink>
            <Button
              type="primary"
              onClick={handleCreate}
              data-testid="save-btn"
            >
              Enable
            </Button>
          </Space>
        </Flex>
      )}
    </ConfigurationCard>
  );
};

export default FidesChatForm;
