import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const OKTA_INTEGRATION_PLACEHOLDER = {
  name: "Okta",
  key: "okta_placeholder",
  connection_type: ConnectionType.OKTA,
  access: AccessLevel.READ,
  created_at: "",
};

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
  category: ConnectionCategory.DATABASE,
  tags: OKTA_TAGS,
  overview: <OktaIntegrationOverview />,
};

export default OKTA_INTEGRATION_TYPE_INFO;
