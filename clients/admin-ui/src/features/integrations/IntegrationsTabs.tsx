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
    <Button size="sm" variant="outline" data-testid="manage-integration">
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
}) => (
  <Box marginTop="24px">
    {integrations.length ? (
      integrations.map((item) => (
        <IntegrationBox
          key={item.key}
          integration={item}
          showTestNotice
          button={<ManageIntegrationButton integrationKey={item.key} />}
        />
      ))
    ) : (
      <NoIntegrations onOpenAddModal={onOpenAddModal} />
    )}
  </Box>
);

export default IntegrationsTabs;
