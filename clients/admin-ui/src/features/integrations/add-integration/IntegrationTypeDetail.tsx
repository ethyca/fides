import { AntButton as Button, Flex, Spacer } from "fidesui";

import { BackButtonNonLink } from "~/features/common/nav/BackButton";
import { IntegrationTypeInfo } from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";

const IntegrationTypeDetail = ({
  integrationType,
  onConfigure,
  onCancel,
  onBack,
}: {
  integrationType?: IntegrationTypeInfo;
  onConfigure: () => void;
  onCancel: () => void;
  onBack: () => void;
}) => (
  <>
    <IntegrationBox
      integration={integrationType?.placeholder}
      onConfigureClick={onConfigure}
    />
    {integrationType?.overview}
    <Flex>
      <div className="mt-8">
        <BackButtonNonLink onClick={onBack} />
      </div>
      <Spacer />
      <Button onClick={onCancel}>Cancel</Button>
    </Flex>
  </>
);

export default IntegrationTypeDetail;
