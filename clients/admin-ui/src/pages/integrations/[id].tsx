import {
  AntCol as Col,
  AntRow as Row,
  AntTabs as Tabs,
  Spinner,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import {
  FEATURE_TAB_KEYS,
  useFeatureBasedTabs,
} from "~/features/integrations/hooks/useFeatureBasedTabs";
import { useIntegrationAuthorization } from "~/features/integrations/hooks/useIntegrationAuthorization";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { IntegrationSetupSteps } from "~/features/integrations/setup-steps/IntegrationSetupSteps";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { ConnectionType } from "~/types/api";

const IntegrationDetailView: NextPage = () => {
  const router = useRouter();
  const id = router.query.id as string;

  const { data: connection, isLoading } = useGetDatastoreConnectionByKeyQuery(
    id,
    {
      skip: !id,
    },
  );

  // Fetch connection types for SAAS integration generation
  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = connectionTypesData?.items || [];

  const integrationOption = useIntegrationOption(
    connection?.connection_type,
    connection?.saas_config?.type as SaasConnectionTypes,
  );

  const {
    testData,
    testConnection,
    isLoading: isTestLoading,
  } = useTestConnection(connection);

  const { handleAuthorize, needsAuthorization } = useIntegrationAuthorization({
    connection,
    connectionOption: integrationOption,
    testData,
  });

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

  const supportsConnectionTest =
    connection?.connection_type !== ConnectionType.MANUAL_TASK;

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
  });

  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: FEATURE_TAB_KEYS,
  });

  return (
    <Layout title="Integrations">
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
          />
          {isLoading ? (
            <Spinner />
          ) : (
            !!connection &&
            !!tabs &&
            tabs.length > 0 && (
              <Tabs
                items={[...tabs]}
                activeKey={activeTab}
                onChange={(tabKey) => {
                  const systemKey = FEATURE_TAB_KEYS.find(
                    (st) => st === tabKey,
                  );

                  if (systemKey) {
                    onTabChange(systemKey);
                  }
                }}
              />
            )
          )}
        </Col>
        <Col flex="0 0 350px">
          {isLoading ? (
            <Spinner />
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
    </Layout>
  );
};

export default IntegrationDetailView;
