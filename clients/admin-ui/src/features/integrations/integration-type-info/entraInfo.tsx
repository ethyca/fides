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
    Microsoft Entra ID (formerly Azure Active Directory) manages identity and
    access for your organization. Adding Entra ID as a data source allows you to
    discover enterprise applications (service principals), monitor access
    patterns, and enhance your data map for better visibility and control.
  </>
);

export const ENTRA_AUTH_DESCRIPTION =
  "Entra ID integration uses OAuth2 Client Credentials for authentication. You will need to register an application in the Azure Portal and provide the tenant ID, client ID, and client secret.";

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
