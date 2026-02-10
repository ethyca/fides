import {
  Button,
  ChakraSpinner as Spinner,
  Col,
  Modal,
  Row,
  Tabs,
  useMessage,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import { getErrorMessage } from "~/features/common/helpers";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import { useDeleteConnectorTemplateMutation } from "~/features/connector-templates/connector-template.slice";
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
  const id = router.query.id as string;

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

  const [modalApi, modalContext] = Modal.useModal();
  const messageApi = useMessage();
  const [deleteConnectorTemplate] = useDeleteConnectorTemplateMutation();

  const handleRemoveCustomIntegration = () => {
    modalApi.confirm({
      title: "Remove",
      icon: null,
      content: (
        <>
          This will remove the custom integration template and update all
          systems and connections that use it. All instances will revert to the
          Fides-provided default integration template.
          <br />
          <br />
          This change applies globally and cannot be undone. Are you sure you
          want to proceed?
        </>
      ),
      okText: "Remove",
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        if (integrationOption?.identifier) {
          try {
            await deleteConnectorTemplate(
              integrationOption.identifier,
            ).unwrap();
          } catch (deleteError) {
            messageApi.error(getErrorMessage(deleteError as any));
          }
        }
      },
    });
  };

  const showRemoveCustomButton =
    !!integrationOption?.custom &&
    !!integrationOption?.default_connector_available;

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
    tabKeys: tabs.map((tab) => tab.key),
  });

  if (error) {
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
            <Spinner />
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
    </FixedLayout>
  );
};

export default IntegrationDetailView;
