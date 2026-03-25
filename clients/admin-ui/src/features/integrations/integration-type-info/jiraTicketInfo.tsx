import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { AccessLevel } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";
import { ConnectionType } from "~/types/api/models/ConnectionType";
import { IntegrationFeature } from "~/types/api/models/IntegrationFeature";

export const JIRA_TICKET_PLACEHOLDER = {
  name: "Jira for Ticketing",
  key: "jira_ticket_placeholder",
  connection_type: ConnectionType.JIRA_TICKET,
  access: AccessLevel.WRITE,
  created_at: "",
};

const JiraTicketOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      The Jira integration enables Fides to automatically create Jira tickets
      when privacy requests are submitted. Tickets are tracked through their
      lifecycle, and the privacy request is resolved when all associated Jira
      tickets are closed.
    </InfoText>
    <InfoText>
      Connect to Jira via OAuth to authorize Fides to create and monitor tickets
      on your behalf.
    </InfoText>
  </>
);

const JIRA_TICKET_TAGS = ["Ticketing"];

const JIRA_TICKET_TYPE_INFO = {
  placeholder: JIRA_TICKET_PLACEHOLDER,
  category: ConnectionCategory.MANUAL,
  tags: JIRA_TICKET_TAGS,
  overview: <JiraTicketOverview />,
  enabledFeatures: [IntegrationFeature.DSR_AUTOMATION],
};

export default JIRA_TICKET_TYPE_INFO;
