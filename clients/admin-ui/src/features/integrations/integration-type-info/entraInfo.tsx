import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { AccessLevel } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";
import { ConnectionType } from "~/types/api/models/ConnectionType";
import { IntegrationFeature } from "~/types/api/models/IntegrationFeature";

export const ENTRA_INTEGRATION_PLACEHOLDER = {
  name: "Microsoft Entra ID",
  key: "entra_placeholder",
  connection_type: ConnectionType.ENTRA,
  access: AccessLevel.READ,
  created_at: "",
};

export const ENTRA_DESCRIPTION = (
  <>
    Identity providers manage user authentication and can help identify systems
    within your infrastructure. Microsoft Entra ID (formerly Azure AD) as a
    data source allows you to detect connected systems, monitor access patterns,
    and enhance your data map for better visibility and control.
  </>
);

export const ENTRA_AUTH_DESCRIPTION =
  "Entra integration uses OAuth2 Client Credentials. You will need an App registration in Microsoft Entra with client ID, client secret (use the secret value, not the secret ID), and tenant ID.";

const EntraIntegrationOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>{ENTRA_DESCRIPTION}</InfoText>
    <InfoText>
      <strong>Authentication:</strong> {ENTRA_AUTH_DESCRIPTION}
    </InfoText>
  </>
);

const ENTRA_TAGS = ["Discovery", "Inventory"];

const ENTRA_INTEGRATION_TYPE_INFO = {
  placeholder: ENTRA_INTEGRATION_PLACEHOLDER,
  category: ConnectionCategory.IDENTITY_PROVIDER,
  tags: ENTRA_TAGS,
  overview: <EntraIntegrationOverview />,
  description: ENTRA_DESCRIPTION,
  enabledFeatures: [IntegrationFeature.DATA_DISCOVERY],
};

export default ENTRA_INTEGRATION_TYPE_INFO;
