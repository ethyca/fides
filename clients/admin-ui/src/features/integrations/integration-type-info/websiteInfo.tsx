import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
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
      Websites, or “properties”, often process user data. Adding a website as an
      integration lets you configure a Consent Management Platform (CMP), a
      site-specific privacy center, and Cross-Origin requests via Fides. You can
      also set up monitors to detect vendors, track technologies like cookies or
      pixels, and ensure compliance.
    </InfoText>
  </>
);

const WEBSITE_INTEGRATION_TYPE_INFO = {
  placeholder: WEBSITE_INTEGRATION_PLACEHOLDER,
  category: ConnectionCategory.WEBSITE,
  tags: ["Website", "Discovery", "Inventory"],
  overview: <WebsiteIntegrationOverview />,
};

export default WEBSITE_INTEGRATION_TYPE_INFO;
