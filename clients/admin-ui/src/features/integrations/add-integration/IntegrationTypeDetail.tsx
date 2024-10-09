import { AntButton as Button, Flex, Spacer } from "fidesui";

import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";

const IntegrationTypeDetail = ({
  integrationType,
  onConfigure,
  onCancel,
}: {
  integrationType?: IntegrationTypeInfo;
  onConfigure: () => void;
  onCancel: () => void;
}) => (
  <>
    <IntegrationBox
      integration={integrationType?.placeholder}
      onConfigureClick={onConfigure}
    />
    {integrationType?.overview}
    <Flex>
      <Spacer />
      <Button onClick={onCancel}>Cancel</Button>
    </Flex>
  </>
);

export default IntegrationTypeDetail;
