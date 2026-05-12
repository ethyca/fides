import {
  Alert,
  Button,
  Card,
  Flex,
  Select,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useJiraAuthorization } from "~/features/integrations/hooks/useJiraAuthorization";
import {
  useGetJiraCredentialLinkStatusQuery,
  useGetJiraSaasConnectionsQuery,
  useLinkJiraSaasCredentialsMutation,
  useUnlinkJiraSaasCredentialsMutation,
} from "~/features/plus/plus.slice";
import {
  ConnectionConfigurationResponse,
  JiraCredentialLinkStatus,
} from "~/types/api";
import { RTKErrorResult } from "~/types/errors";

interface JiraCredentialsTabProps {
  connection: ConnectionConfigurationResponse;
  testData: {
    authorized?: boolean;
  };
}

enum SyncStatus {
  SYNCED = "synced",
  STALE = "stale",
  SOURCE_MISSING = "source_missing",
}

const SYNC_STATUS_CONFIG: Record<
  NonNullable<JiraCredentialLinkStatus["sync_status"]>,
  { label: string; color: "success" | "warning" | "error" }
> = {
  synced: { label: "Synced", color: "success" },
  stale: { label: "Stale", color: "warning" },
  source_missing: { label: "Source missing", color: "error" },
};

const JiraCredentialsTab = ({
  connection,
  testData,
}: JiraCredentialsTabProps) => {
  const msgApi = useMessage();
  const [selectedSaasKey, setSelectedSaasKey] = useState<string | undefined>();

  const { handleAuthorize, isLoading: isOAuthLoading } = useJiraAuthorization({
    connection,
    testData,
  });

  const { data: linkStatus, isLoading: isStatusLoading } =
    useGetJiraCredentialLinkStatusQuery(
      { connectionKey: connection.key },
      { skip: !connection.key },
    );

  const { data: saasConnections, isLoading: isSaasLoading } =
    useGetJiraSaasConnectionsQuery(
      { connectionKey: connection.key },
      { skip: !connection.key },
    );

  const [linkCredentials, { isLoading: isLinking }] =
    useLinkJiraSaasCredentialsMutation();

  const [unlinkCredentials, { isLoading: isUnlinking }] =
    useUnlinkJiraSaasCredentialsMutation();

  const handleLink = async () => {
    if (!selectedSaasKey) {
      return;
    }
    try {
      await linkCredentials({
        connectionKey: connection.key,
        saas_connection_key: selectedSaasKey,
      }).unwrap();
      msgApi.success("Jira credentials linked successfully");
      setSelectedSaasKey(undefined);
    } catch (error) {
      msgApi.error(getErrorMessage(error as RTKErrorResult["error"]));
    }
  };

  const handleUnlink = async () => {
    try {
      await unlinkCredentials({
        connectionKey: connection.key,
      }).unwrap();
      msgApi.success("Jira credentials unlinked");
    } catch (error) {
      msgApi.error(getErrorMessage(error as RTKErrorResult["error"]));
    }
  };

  const isLinked = linkStatus?.is_linked ?? false;
  const syncStatus = linkStatus?.sync_status;

  return (
    <Flex vertical gap="middle" className="max-w-screen-md pt-4">
      <Typography.Paragraph type="secondary">
        Configure how Fides authenticates with your Jira instance. You can
        authorize via OAuth or link credentials from an existing Jira connector.
      </Typography.Paragraph>

      {/* Current status */}
      {!isStatusLoading && linkStatus && (
        <Card size="small" title="Credential status">
          {isLinked ? (
            <Flex vertical gap="small">
              <Flex align="center" gap="small">
                <Typography.Text>
                  Linked to{" "}
                  <Typography.Text strong>
                    {linkStatus.linked_saas_name}
                  </Typography.Text>
                </Typography.Text>
                {syncStatus && SYNC_STATUS_CONFIG[syncStatus] && (
                  <Tag color={SYNC_STATUS_CONFIG[syncStatus].color}>
                    {SYNC_STATUS_CONFIG[syncStatus].label}
                  </Tag>
                )}
              </Flex>
              {syncStatus === SyncStatus.STALE && (
                <Alert
                  type="warning"
                  title="Credentials may be out of date. Re-link to sync the latest credentials from the source connector."
                  showIcon
                />
              )}
              {syncStatus === SyncStatus.SOURCE_MISSING && (
                <Alert
                  type="error"
                  title="The source connector has been removed. Unlink and choose a new source, or authorize via OAuth."
                  showIcon
                />
              )}
              <Flex>
                <Button
                  danger
                  onClick={handleUnlink}
                  loading={isUnlinking}
                  data-testid="unlink-jira-credentials-btn"
                >
                  Unlink credentials
                </Button>
              </Flex>
            </Flex>
          ) : (
            <Typography.Text type="secondary">
              {testData.authorized
                ? "Authorized via OAuth"
                : "No credentials configured"}
            </Typography.Text>
          )}
        </Card>
      )}

      {/* OAuth authorization */}
      <Card size="small" title="OAuth authorization">
        <Flex vertical gap="small">
          <Typography.Text type="secondary">
            Authorize Fides to access your Jira instance using your Atlassian
            account.
          </Typography.Text>
          <Flex>
            <Button
              onClick={handleAuthorize}
              loading={isOAuthLoading}
              data-testid="jira-oauth-authorize-btn"
            >
              Authorize with Jira
            </Button>
          </Flex>
        </Flex>
      </Card>

      {/* SaaS credential linking */}
      <Card size="small" title="Link from existing connector">
        <Flex vertical gap="small">
          <Typography.Text type="secondary">
            Copy API key credentials from an existing Jira SaaS connector.
          </Typography.Text>
          {saasConnections && saasConnections.length > 0 ? (
            <Flex gap="middle" align="end">
              <Select
                aria-label="Jira connector"
                className="min-w-[250px]"
                placeholder="Select a Jira connector"
                loading={isSaasLoading}
                value={selectedSaasKey}
                onChange={setSelectedSaasKey}
                data-testid="jira-saas-connector-select"
                options={saasConnections.map((c) => ({
                  value: c.key,
                  label: c.name,
                }))}
              />
              <Button
                type="primary"
                onClick={handleLink}
                loading={isLinking}
                disabled={!selectedSaasKey}
                data-testid="link-jira-credentials-btn"
              >
                Link credentials
              </Button>
            </Flex>
          ) : (
            <Typography.Text type="secondary">
              {isSaasLoading
                ? "Loading connectors..."
                : "No Jira SaaS connectors available for linking."}
            </Typography.Text>
          )}
        </Flex>
      </Card>
    </Flex>
  );
};

export default JiraCredentialsTab;
