import { Box } from "fidesui";
import { useRouter } from "next/router";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import NoIntegrations from "~/features/integrations/NoIntegrations";
import { ConnectionConfigurationResponse } from "~/types/api";

const IntegrationsTabs = ({
  integrations,
  onOpenAddModal,
}: {
  integrations: ConnectionConfigurationResponse[];
  onOpenAddModal: () => void;
}) => {
  const router = useRouter();
  return (
    <Box marginTop="24px">
      {integrations.length ? (
        integrations.map((item) => (
          <IntegrationBox
            key={item.key}
            integration={item}
            showTestNotice
            configureButtonLabel="Manage"
            onConfigureClick={() =>
              router.push(`${INTEGRATION_MANAGEMENT_ROUTE}/${item.key}`)
            }
          />
        ))
      ) : (
        <NoIntegrations onOpenAddModal={onOpenAddModal} />
      )}
    </Box>
  );
};

export default IntegrationsTabs;
