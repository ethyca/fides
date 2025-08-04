import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoOrderedList,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel } from "~/types/api";
import { ConnectionType } from "~/types/api/models/ConnectionType";

import { IntegrationFeatureEnum } from "../IntegrationFeatureEnum";

export const JIRA_PLACEHOLDER = {
  name: "Jira",
  key: "jira_placeholder",
  connection_type: ConnectionType.JIRA,
  access: AccessLevel.WRITE,
  created_at: "",
};

export const JIRA_TAGS = ["DSR", "Automated tasks"];

export const JiraOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Jira is a project management and issue tracking tool developed by
      Atlassian. Connect Fides to your Jira instance to automatically create
      tickets for Data Subject Requests (DSRs) and other automated tasks,
      ensuring proper tracking and workflow management for privacy operations.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="What this integration does" />
      <InfoUnorderedList>
        <ListItem>
          Automatically create Jira tickets for incoming Data Subject Requests
        </ListItem>
        <ListItem>
          Track DSR progress and status updates within Jira workflows
        </ListItem>
        <ListItem>
          Create automated tasks for privacy compliance activities
        </ListItem>
        <ListItem>
          Assign tickets to appropriate team members for manual review
        </ListItem>
        <ListItem>Maintain audit trails for privacy request handling</ListItem>
      </InfoUnorderedList>
      <InfoText>
        Once integrated, the system will automatically create and manage Jira
        tickets for privacy requests, ensuring proper tracking and
        accountability for your privacy operations team.
      </InfoText>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>Task Management</ListItem>
        <ListItem>Privacy Operations</ListItem>
        <ListItem>Workflow Automation</ListItem>
        <ListItem>Audit Tracking</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Prerequisites" />
      <InfoText>
        To integrate with Jira, you need administrative access to your Jira
        instance and the ability to create API tokens or OAuth applications for
        secure connectivity.
      </InfoText>
      <InfoHeading text="Setup instructions" />
      <InfoText>Follow these steps to set up your Jira integration:</InfoText>
      <InfoOrderedList>
        <ListItem>Log into your Jira instance as an administrator</ListItem>
        <ListItem>
          Create an API token in your Atlassian account settings
        </ListItem>
        <ListItem>
          Configure project permissions for the integration user
        </ListItem>
        <ListItem>Set up issue types and workflows for DSR tracking</ListItem>
        <ListItem>Test the connection to ensure proper authentication</ListItem>
      </InfoOrderedList>
      <InfoHeading text="Required information" />
      <InfoUnorderedList>
        <ListItem>Jira Instance URL: Your Jira server or cloud URL</ListItem>
        <ListItem>
          Username/Email: Account with appropriate permissions
        </ListItem>
        <ListItem>
          API Token: Generated from Atlassian account settings
        </ListItem>
        <ListItem>Project Key: Target project for creating tickets</ListItem>
        <ListItem>Issue Type: Default issue type for DSR tickets</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Supported features" />
      <InfoUnorderedList>
        <ListItem>Create tickets for Data Subject Requests</ListItem>
        <ListItem>Update ticket status based on DSR progress</ListItem>
        <ListItem>Assign tickets to team members</ListItem>
        <ListItem>Add comments and attachments</ListItem>
        <ListItem>Custom field mapping</ListItem>
        <ListItem>Workflow automation</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const JIRA_TYPE_INFO = {
  placeholder: JIRA_PLACEHOLDER,
  category: ConnectionCategory.TASK_MANAGEMENT,
  overview: <JiraOverview />,
  tags: JIRA_TAGS,
  enabledFeatures: [IntegrationFeatureEnum.TASKS],
};

export default JIRA_TYPE_INFO;
