import { AntFlex, AntTabs as Tabs, Spinner } from "fidesui";
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
import { useFeatureBasedTabs } from "~/features/integrations/hooks/useFeatureBasedTabs";
import { useIntegrationAuthorization } from "~/features/integrations/hooks/useIntegrationAuthorization";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { IntegrationSetupSteps } from "~/features/integrations/setup-steps/IntegrationSetupSteps";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { ConnectionType } from "~/types/api";

const IntegrationDetailView: NextPage = () => {
  const router = useRouter();
  const id = Array.isArray(router.query.id)
    ? router.query.id[0]
    : router.query.id;

  const { data: connection, isLoading } = useGetDatastoreConnectionByKeyQuery(
    id!,
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

  const { overview, instructions, description, enabledFeatures } =
    getIntegrationTypeInfo(
      connection?.connection_type,
      connection?.saas_config?.type,
      connectionTypes,
    );

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
    tabKeys: tabs.map((tab) => tab.key),
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
      >
        <AntFlex gap={24}>
          <div className="grow">
            <div className="mb-6">
              <IntegrationBox integration={connection} showDeleteButton />
            </div>
            {isLoading ? (
              <Spinner />
            ) : (
              !!connection && (
                <Tabs
                  items={tabs}
                  activeKey={activeTab}
                  onChange={onTabChange}
                />
              )
            )}
          </div>
          <div className="w-[350px] shrink-0">
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
          </div>
        </AntFlex>
      </PageHeader>
    </Layout>
  );
};

export default IntegrationDetailView;
