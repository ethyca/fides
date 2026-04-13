import { Typography } from "fidesui";

import {
  InfoHeading,
  InfoOrderedList,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { AccessLevel, ConnectionType } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";
import { IntegrationFeature } from "~/types/api/models/IntegrationFeature";

const GW_PLACEHOLDER = {
  name: "Google Workspace",
  key: "google_workspace_placeholder",
  connection_type: ConnectionType.GOOGLE_WORKSPACE,
  access: AccessLevel.READ,
  created_at: "",
};

const GOOGLE_WORKSPACE_TAGS = ["Identity", "Google Groups"];

const GoogleWorkspaceOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Connect Google Workspace to resolve user identities via Google Groups
      membership. This enables purpose-based access control (PBAC) to map query
      authors to data consumers based on their group memberships.
    </InfoText>
    <InfoUnorderedList>
      <li>Resolves Google Group memberships via Cloud Identity API</li>
      <li>Requires a service account with domain-wide delegation configured</li>
      <li>Maps group memberships to data consumer purposes</li>
    </InfoUnorderedList>
  </>
);

const GoogleWorkspaceInstructions = () => (
  <ShowMoreContent>
    <InfoHeading text="Step 1: Create a GCP service account" />
    <InfoText>
      Create a service account in your GCP project for Google Workspace identity
      resolution.
    </InfoText>
    <InfoHeading text="Step 2: Enable the Cloud Identity API" />
    <InfoOrderedList>
      <li>
        Go to the{" "}
        <Typography.Link
          href="https://console.cloud.google.com/apis/library/cloudidentity.googleapis.com"
          target="_blank"
        >
          Cloud Identity API page
        </Typography.Link>
      </li>
      <li>Click &quot;Enable&quot;</li>
    </InfoOrderedList>
    <InfoHeading text="Step 3: Configure domain-wide delegation" />
    <InfoOrderedList>
      <li>
        In the Google Admin Console, navigate to Security &gt; Access and data
        control &gt; API controls &gt; Manage Domain-wide Delegation
      </li>
      <li>Add a new client ID using the service account OAuth2 client ID</li>
      <li>
        Add the scope:{" "}
        <code>
          https://www.googleapis.com/auth/cloud-identity.groups.readonly
        </code>
      </li>
    </InfoOrderedList>
    <InfoHeading text="Step 4: Generate a JSON keyfile" />
    <InfoText>
      Download the service account JSON keyfile and provide it along with the
      delegation subject (a Workspace admin email) and your domain.
    </InfoText>
  </ShowMoreContent>
);

const GOOGLE_WORKSPACE_TYPE_INFO = {
  placeholder: GW_PLACEHOLDER,
  category: ConnectionCategory.IDENTITY_PROVIDER,
  overview: <GoogleWorkspaceOverview />,
  instructions: <GoogleWorkspaceInstructions />,
  tags: GOOGLE_WORKSPACE_TAGS,
  enabledFeatures: [IntegrationFeature.IDENTITY_RESOLUTION],
};

export default GOOGLE_WORKSPACE_TYPE_INFO;
