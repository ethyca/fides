import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";

const IntegrationTypeDetail = ({
  integrationType,
  onConfigure,
}: {
  integrationType?: IntegrationTypeInfo;
  onConfigure: () => void;
}) => (
  <>
    <IntegrationBox
      integration={integrationType?.placeholder}
      onConfigureClick={onConfigure}
    />
    {integrationType?.overview}
  </>
);

export default IntegrationTypeDetail;
