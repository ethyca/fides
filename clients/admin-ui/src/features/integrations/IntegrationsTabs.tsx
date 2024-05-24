import { Box, Button } from "fidesui";
import NextLink from "next/link";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import NoIntegrations from "~/features/integrations/NoIntegrations";
import { ConnectionConfigurationResponse } from "~/types/api";

const ManageIntegrationButton = ({
  integrationKey,
}: {
  integrationKey: string;
}) => (
  <NextLink href={`${INTEGRATION_MANAGEMENT_ROUTE}/${integrationKey}`}>
    <Button size="sm" variant="outline">
      Manage
    </Button>
  </NextLink>
);

const IntegrationsTabs = ({
  integrations,
  onOpenAddModal,
}: {
  integrations: ConnectionConfigurationResponse[];
  onOpenAddModal: () => void;
}) => {
  const renderIntegration = (item: ConnectionConfigurationResponse) => (
    <IntegrationBox
      key={item.key}
      integration={item}
      renderTestNotice
      button={<ManageIntegrationButton integrationKey={item.key} />}
    />
  );

  return (
    <Box marginTop="24px">
      {integrations.length ? (
        integrations.map(renderIntegration)
      ) : (
        <NoIntegrations onOpenAddModal={onOpenAddModal} />
      )}
    </Box>
  );
};

export default IntegrationsTabs;
