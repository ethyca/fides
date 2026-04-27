import { Alert, Button, Flex, Icons, Space, Typography, useMessage } from "fidesui";
import { useRouter } from "next/router";

import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import type { ChatConfigCreate } from "~/types/api";

import {
  useCreateChatConfigMutation,
  useGetChatConfigQuery,
} from "../chatProvider.slice";
import AuthorizationStatus from "../components/AuthorizationStatus";
import ConfigurationCard from "../components/ConfigurationCard";

const { Text } = Typography;

interface TerminalChatFormProps {
  configId?: string;
}

const TerminalChatForm = ({ configId }: TerminalChatFormProps) => {
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
      const payload: ChatConfigCreate = {
        provider_type: "terminal",
      };

      const result = await createConfig(payload);

      if (isErrorResult(result)) {
        handleError(result.error);
      } else if ("data" in result && result.data) {
        message.success("Terminal provider enabled.");
        router.push(`${CHAT_PROVIDERS_ROUTE}/configure?id=${result.data.id}`);
      }
    } catch (error) {
      handleError(error);
    }
  };

  return (
    <ConfigurationCard
      title="Terminal chat provider"
      icon={<Icons.Checkmark />}
    >
      <Space orientation="vertical" size="medium" className="w-full">
        <Alert
          type="info"
          showIcon
          description={
            <Text>
              The Terminal provider lets you run questionnaire conversations
              from a terminal using the CLI chat script. Answers are persisted
              to the database and progress is visible in the Admin UI.
            </Text>
          }
          message="How it works"
        />

        <Alert
          type="warning"
          showIcon
          description={
            <Text>
              Start a questionnaire conversation from the terminal. You can
              launch one from any assessment detail page.
            </Text>
          }
          message="How to start a conversation"
        />

        {isEditMode && isAuthorized && (
          <AuthorizationStatus authorized />
        )}
      </Space>

      {!isEditMode && (
        <Flex justify="flex-end" className="mt-6">
          <Space>
            <Button
              onClick={() => router.push(CHAT_PROVIDERS_ROUTE)}
              data-testid="cancel-btn"
            >
              Cancel
            </Button>
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

export default TerminalChatForm;
