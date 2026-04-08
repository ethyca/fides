import { Button, Col, Row, Spin, Tabs, useMessage } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useRef } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFlags } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import { useFeatureBasedTabs } from "~/features/integrations/hooks/useFeatureBasedTabs";
import { useIntegrationAuthorization } from "~/features/integrations/hooks/useIntegrationAuthorization";
import { useJiraAuthorization } from "~/features/integrations/hooks/useJiraAuthorization";
import { useRemoveCustomIntegration } from "~/features/integrations/hooks/useRemoveCustomIntegration";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { IntegrationSetupSteps } from "~/features/integrations/setup-steps/IntegrationSetupSteps";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { ConnectionType } from "~/types/api";

const IntegrationDetailView: NextPage = () => {
  const router = useRouter();
  const id = router.query.id as string;
  const message = useMessage();
  const oauthHandled = useRef(false);

  const {
    flags: { alphaJiraIntegration },
  } = useFlags();

  const {
    data: connection,
    isLoading,
    error,
  } = useGetDatastoreConnectionByKeyQuery(id, {
    skip: !id,
  });

  // Fetch connection types for SAAS integration generation
  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = connectionTypesData?.items || [];

  const integrationOption = useIntegrationOption(
    connection?.connection_type,
    connection?.saas_config?.type as SaasConnectionTypes,
  );

  const { handleRemove: handleRemoveCustomIntegration, modalContext } =
    useRemoveCustomIntegration(integrationOption);

  const showRemoveCustomButton =
    !!integrationOption?.custom &&
    !!integrationOption?.default_connector_available;

  const {
    testData,
    testConnection,
    isLoading: isTestLoading,
  } = useTestConnection(connection);

  const isJira = connection?.connection_type === ConnectionType.JIRA_TICKET;

  const defaultAuth = useIntegrationAuthorization({
    connection,
    connectionOption: integrationOption,
    testData,
  });

  const jiraAuth = useJiraAuthorization({
    connection,
    testData,
  });

  const { handleAuthorize, needsAuthorization } = isJira
    ? jiraAuth
    : defaultAuth;

  // Handle OAuth callback query params
  useEffect(() => {
    if (oauthHandled.current) {
      return;
    }
    const jiraAuthStatus = router.query.jira_auth as string | undefined;
    if (jiraAuthStatus === "success") {
      oauthHandled.current = true;
      message.success("Jira authorization successful");
      router.replace(`${INTEGRATION_MANAGEMENT_ROUTE}/${id}`, undefined, {
        shallow: true,
      });
    } else if (jiraAuthStatus === "error") {
      oauthHandled.current = true;
      message.error(
        "Jira authorization failed. Check server logs for details.",
      );
      router.replace(`${INTEGRATION_MANAGEMENT_ROUTE}/${id}`, undefined, {
        shallow: true,
      });
    }
  }, [router.query.jira_auth, id, message, router]);

  const integrationTypeInfo = getIntegrationTypeInfo(
    connection?.connection_type,
    connection?.saas_config?.type,
    connectionTypes,
  );

  const { overview, instructions, description, enabledFeatures } =
    integrationTypeInfo;

  if (
    !!connection &&
    !SUPPORTED_INTEGRATIONS.includes(connection.connection_type)
  ) {
    router.push(INTEGRATION_MANAGEMENT_ROUTE);
  }

  if (
    !!connection &&
    connection.connection_type === ConnectionType.JIRA_TICKET &&
    !alphaJiraIntegration
  ) {
    router.push(INTEGRATION_MANAGEMENT_ROUTE);
  }

  const supportsConnectionTest =
    connection?.connection_type !== ConnectionType.MANUAL_TASK;

  const supportsSystemLinking =
    connection?.connection_type !== ConnectionType.WEBSITE &&
    connection?.connection_type !== ConnectionType.MANUAL_TASK &&
    connection?.connection_type !== ConnectionType.JIRA_TICKET;

  const tabs = useFeatureBasedTabs({
    connection,
    enabledFeatures,
    integrationOption,
    testData,
    needsAuthorization,
    handleAuthorize,
    testConnection,
    testIsLoading: isTestLoading,
    description,
    overview,
    instructions,
    supportsConnectionTest,
    supportsSystemLinking,
  });

  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: tabs.map((tab) => tab.key),
  });

  const isAbortedRequest =
    error && "status" in error && error.status === "FETCH_ERROR";
  if (error && !isAbortedRequest) {
    return (
      <ErrorPage
        error={error}
        defaultMessage={`A problem occurred while fetching the integration ${id}`}
        actions={[
          {
            label: "Return to integrations",
            onClick: () => router.push(INTEGRATION_MANAGEMENT_ROUTE),
          },
        ]}
      />
    );
  }

  return (
    <FixedLayout title="Integrations">
      <PageHeader
        heading="Integrations"
        breadcrumbItems={[
          {
            title: "All integrations",
            href: INTEGRATION_MANAGEMENT_ROUTE,
          },
          {
            title: connection?.name ?? connection?.key ?? "",
          },
        ]}
      />
      <Row wrap={false} gutter={24}>
        <Col flex="1 1 auto">
          <IntegrationBox
            integration={connection}
            integrationTypeInfo={integrationTypeInfo}
            showDeleteButton
            otherButtons={
              showRemoveCustomButton ? (
                <Button
                  type="link"
                  danger
                  data-testid="remove-custom-integration-btn"
                  onClick={handleRemoveCustomIntegration}
                >
                  Remove
                </Button>
              ) : undefined
            }
          />
          {modalContext}
          {isLoading ? (
            <Spin />
          ) : (
            !!connection && (
              <Tabs items={tabs} activeKey={activeTab} onChange={onTabChange} />
            )
          )}
        </Col>
        <Col
          xs={{ flex: "0 0 310px" }}
          xl={{ flex: "0 0 330px" }}
          xxl={{ flex: "0 0 350px" }}
        >
          {isLoading ? (
            <Spin />
          ) : (
            !!connection && (
              <IntegrationSetupSteps
                testData={testData}
                testIsLoading={isTestLoading}
                connectionOption={integrationOption!}
                connection={connection}
              />
            )
          )}
        </Col>
      </Row>
    </FixedLayout>
  );
};

export default IntegrationDetailView;
