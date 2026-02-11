import { Button } from "fidesui";

import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";
import { useRemoveCustomIntegration } from "~/features/integrations/hooks/useRemoveCustomIntegration";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";

const IntegrationTypeDetail = ({
  integrationType,
  onConfigure,
}: {
  integrationType?: IntegrationTypeInfo;
  onConfigure: () => void;
}) => {
  const connectionOption = useIntegrationOption(
    integrationType?.placeholder.connection_type,
    integrationType?.placeholder.saas_config?.type as SaasConnectionTypes,
  );

  const { handleRemove: handleRemoveCustomIntegration, modalContext } =
    useRemoveCustomIntegration(connectionOption);

  const showRemoveButton =
    !!connectionOption?.custom &&
    !!connectionOption?.default_connector_available;

  return (
    <>
      {modalContext}
      <IntegrationBox
        integration={integrationType?.placeholder}
        integrationTypeInfo={integrationType}
        onConfigureClick={onConfigure}
        otherButtons={
          showRemoveButton ? (
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
      {integrationType?.overview}
    </>
  );
};

export default IntegrationTypeDetail;
