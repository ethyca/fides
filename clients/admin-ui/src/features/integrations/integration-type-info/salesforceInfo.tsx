import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoOrderedList,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import { AccessLevel } from "~/types/api";
import { ConnectionType } from "~/types/api/models/ConnectionType";

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
      <InfoHeading text="What this integration does" />
      <InfoUnorderedList>
        <ListItem>
          Discover personal data in standard Salesforce objects
        </ListItem>
        <ListItem>
          Detect sensitive information across your Salesforce instance
        </ListItem>
        <ListItem>
          Automate data subject access requests including data retrieval,
          updates, and deletions
        </ListItem>
        <ListItem>
          Map Salesforce data to your organization&apos;s data map
        </ListItem>
        <ListItem>
          Discover and map custom Salesforce objects (requires setting up a
          monitor)
        </ListItem>
      </InfoUnorderedList>
      <InfoText>
        Once integrated, the system will automatically map sensitive personal
        data for standard Salesforce objects. By setting up a monitor, you can
        also detect and map custom objects in your Salesforce instance.
      </InfoText>
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
      <InfoHeading text="Setup Instructions" />
      <InfoText>
        Follow these steps to set up your Salesforce integration:
      </InfoText>
      <InfoOrderedList>
        <ListItem>
          Create a Connected App in Salesforce by following the Salesforce guide
        </ListItem>
        <ListItem>Configure Basic Connected App Settings</ListItem>
        <ListItem>
          Uncheck &quot;Require Proof Key for Code Exchange (PKCE) Extension for
          Supported Authorization Flows&quot;
        </ListItem>
        <ListItem>
          Enable OAuth Settings for API Integration with the required scopes
        </ListItem>
        <ListItem>
          Enter your Fides Redirect URL (typically
          https://fides-host.com/api/v1/oauth/callback)
        </ListItem>
      </InfoOrderedList>
      <InfoHeading text="Required Information" />
      <InfoUnorderedList>
        <ListItem>Domain: Your Salesforce URL</ListItem>
        <ListItem>Consumer Key: Your OAuth client ID</ListItem>
        <ListItem>Consumer Secret: Your OAuth client secret</ListItem>
        <ListItem>Redirect URL: The Fides URL for OAuth callback</ListItem>
        <ListItem>
          Token Refresh URL: The Salesforce URL for refresh tokens
        </ListItem>
      </InfoUnorderedList>
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
