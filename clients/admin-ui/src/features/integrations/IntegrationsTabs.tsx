import { Box, Button } from "fidesui";
import { NextPage } from "next";
import NextLink from "next/link";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import NoIntegrations from "~/features/integrations/NoIntegrations";

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

const IntegrationsTabs: NextPage = ({ data }) => {
  const renderIntegration = (item) => (
    <IntegrationBox
      key={item.key}
      integration={item}
      renderTestNotice
      button={<ManageIntegrationButton integrationKey={item.key} />}
    />
  );

  const renderNoIntegrations = () => !data.total && <NoIntegrations />;

  return (
    <Box marginTop="24px">
      {data.items.map(renderIntegration)}
      {renderNoIntegrations()}
    </Box>
  );
};

export default IntegrationsTabs;
