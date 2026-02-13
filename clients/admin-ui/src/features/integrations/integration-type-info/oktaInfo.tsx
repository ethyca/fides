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
    Identity providers manage user authentication and can help identify systems
    within your infrastructure. Adding an identity provider as a data source
    allows you to detect connected systems, monitor access patterns, and enhance
    your data map for better visibility and control.
  </>
);

export const OKTA_AUTH_DESCRIPTION =
  "Okta integration uses OAuth2 Client Credentials with private_key_jwt for secure authentication. You will need to generate an RSA key in Okta and copy the JSON key to use in Fides.";

const OktaIntegrationOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>{OKTA_DESCRIPTION}</InfoText>
    <InfoText>
      <strong>Authentication:</strong> {OKTA_AUTH_DESCRIPTION}
    </InfoText>
    <InfoText>
      <strong>Authentication:</strong> Okta integration uses OAuth2 Client
      Credentials with private_key_jwt for secure authentication. You&apos;ll
      need to create an API Services application in Okta and generate an RSA key
      pair.
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
