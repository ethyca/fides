import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { AccessLevel } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";
import { ConnectionType } from "~/types/api/models/ConnectionType";
import { IntegrationFeature } from "~/types/api/models/IntegrationFeature";

export const OKTA_INTEGRATION_PLACEHOLDER = {
  name: "Okta",
  key: "okta_placeholder",
  connection_type: ConnectionType.OKTA,
  access: AccessLevel.READ,
  created_at: "",
};

export const OKTA_DESCRIPTION = (
  <>
    SSO providers manage user authentication and can help identify systems
    within your infrastructure. Adding an SSO provider as a data source allows
    you to detect connected systems, monitor access patterns, and enhance your
    data map for better visibility and control.
  </>
);

const OktaIntegrationOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      SSO providers manage user authentication and can help identify systems
      within your infrastructure. Adding an SSO provider as a data source allows
      you to detect connected systems, monitor access patterns, and enhance your
      data map for better visibility and control.
    </InfoText>
  </>
);

const OKTA_TAGS = ["Discovery", "Inventory"];

const OKTA_INTEGRATION_TYPE_INFO = {
  placeholder: OKTA_INTEGRATION_PLACEHOLDER,
  category: ConnectionCategory.IDENTITY_PROVIDER,
  tags: OKTA_TAGS,
  overview: <OktaIntegrationOverview />,
  description: OKTA_DESCRIPTION,
  enabledFeatures: [IntegrationFeature.DATA_DISCOVERY],
};

export default OKTA_INTEGRATION_TYPE_INFO;
