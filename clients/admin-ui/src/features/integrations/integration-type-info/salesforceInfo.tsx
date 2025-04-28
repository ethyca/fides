import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel } from "~/types/api";
import {
  ConnectionType,
  SaasConnectionTypes,
} from "~/types/api/models/ConnectionType";

export const SALESFORCE_PLACEHOLDER = {
  name: "Salesforce",
  key: "salesforce_placeholder",
  connection_type: ConnectionType.SAAS,
  saas_config: {
    fides_key: "salesforce",
    name: "Salesforce",
    type: SaasConnectionTypes.SALESFORCE,
  },
  access: AccessLevel.WRITE,
  created_at: "",
};

export const SALESFORCE_TAGS = [
  "API",
  "DSR Automation",
  "Discovery",
  "Detection",
];

export const SalesforceOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Salesforce is a cloud-based customer relationship management (CRM)
      platform that helps businesses manage sales, marketing, and customer
      service interactions in a unified system. Connect Fides to your Salesforce
      instance to automatically discover and track data across both standard and
      custom objects, detect sensitive information, and automate DSR
      fulfillment.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>CRM System</ListItem>
        <ListItem>Data detection</ListItem>
        <ListItem>Data discovery</ListItem>
        <ListItem>DSR automation</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Prerequisites" />
      <InfoText>
        To integrate with Salesforce, you need to create a Connected App in your
        Salesforce instance. This ensures exclusive data control and enhances
        security by reducing unauthorized access risks.
      </InfoText>
      <InfoHeading text="Required OAuth Scopes" />
      <InfoUnorderedList>
        <ListItem>Manage user data via APIs (api)</ListItem>
        <ListItem>
          Perform requests at any time (refresh_token, offline_access)
        </ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Supported Objects" />
      <InfoText>
        Fides supports both standard and custom Salesforce objects. The
        integration includes built-in support for common objects such as:
      </InfoText>
      <InfoUnorderedList>
        <ListItem>Contacts</ListItem>
        <ListItem>Cases</ListItem>
        <ListItem>Leads</ListItem>
        <ListItem>Accounts</ListItem>
        <ListItem>Campaign Members</ListItem>
        <ListItem>Custom Objects</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const SALESFORCE_TYPE_INFO = {
  placeholder: SALESFORCE_PLACEHOLDER,
  category: ConnectionCategory.CRM,
  overview: <SalesforceOverview />,
  tags: SALESFORCE_TAGS,
};

export default SALESFORCE_TYPE_INFO;
