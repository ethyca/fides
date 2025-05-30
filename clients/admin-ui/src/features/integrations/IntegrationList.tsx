import { Box } from "fidesui";
import { useRouter } from "next/router";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import getIntegrationTypeInfo from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";
import NoIntegrations from "~/features/integrations/NoIntegrations";
import { ConnectionConfigurationResponse } from "~/types/api";

const IntegrationList = ({
  integrations,
  isFiltered,
  onOpenAddModal,
}: {
  integrations: ConnectionConfigurationResponse[];
  isFiltered?: boolean;
  onOpenAddModal: () => void;
}) => {
  const router = useRouter();
  return (
    <Box marginTop="24px">
      {integrations.length ? (
        integrations.map((item) => {
          const integrationTypeInfo = getIntegrationTypeInfo(
            item.connection_type,
          );
          const showTestNotice = !integrationTypeInfo.enabledFeatures?.includes(
            IntegrationFeatureEnum.WITHOUT_CONNECTION,
          );

          return (
            <IntegrationBox
              key={item.key}
              integration={item}
              showTestNotice={showTestNotice}
              configureButtonLabel="Manage"
              onConfigureClick={() =>
                router.push(`${INTEGRATION_MANAGEMENT_ROUTE}/${item.key}`)
              }
            />
          );
        })
      ) : (
        <NoIntegrations
          onOpenAddModal={onOpenAddModal}
          isFiltered={isFiltered}
        />
      )}
    </Box>
  );
};

export default IntegrationList;
