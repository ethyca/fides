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
      Okta is a cloud-based identity and access management (IAM) service that
      helps organizations manage user authentication and authorization. The Okta
      integration allows you to manage user data, handle authentication
      requests, and ensure compliance with privacy regulations.
    </InfoText>
  </>
);

const OKTA_TAGS = ["Authentication", "User Management", "Identity"];

const OKTA_INTEGRATION_TYPE_INFO = {
  placeholder: OKTA_INTEGRATION_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  tags: OKTA_TAGS,
  overview: <OktaIntegrationOverview />,
};

export default OKTA_INTEGRATION_TYPE_INFO;
