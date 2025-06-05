import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";
import { AccessLevel, ConnectionType } from "~/types/api";

export const WEBSITE_INTEGRATION_PLACEHOLDER = {
  name: "Website",
  key: "website_placeholder",
  connection_type: ConnectionType.WEBSITE,
  access: AccessLevel.READ,
  created_at: "",
};

const WebsiteIntegrationOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Websites, or &quot;properties&quot;, often process user data. Adding a
      website as an integration lets you configure a Consent Management Platform
      (CMP), a site-specific privacy center, and Cross-Origin requests via
      Fides. You can configure the various security settings, styling, and user
      experience settings for the privacy center and CMP on a per-website basis.
    </InfoText>
  </>
);

const WEBSITE_TAGS = ["Consent", "Discovery", "Detection"];

const WEBSITE_INTEGRATION_TYPE_INFO = {
  placeholder: WEBSITE_INTEGRATION_PLACEHOLDER,
  category: ConnectionCategory.WEBSITE,
  tags: WEBSITE_TAGS,
  overview: <WebsiteIntegrationOverview />,
  enabledFeatures: [IntegrationFeatureEnum.DATA_DISCOVERY],
};

export default WEBSITE_INTEGRATION_TYPE_INFO;
