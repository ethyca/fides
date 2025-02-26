import { Code, ListItem } from "fidesui";

import {
  InfoHeading,
  InfoLink,
  InfoOrderedList,
  InfoPermissionsTable,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const DYNAMO_PLACEHOLDER = {
  name: "DynamoDB",
  key: "dynamo_placeholder",
  connection_type: ConnectionType.DYNAMODB,
  access: AccessLevel.READ,
  created_at: "",
};

export const DYNAMO_TAGS = ["Database", "DynamoDB", "Discovery", "Inventory"];

export const DynamoOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Continuously monitor DynamoDB to detect and track schema-level changes,
      automatically discover and label data categories as well as automatically
      process DSR (privacy requests) and consent enforcement to proactively
      manage data governance risks.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>NoSQL database</ListItem>
        <ListItem>Storage system</ListItem>
        <ListItem>Cloud provider</ListItem>
        <ListItem>Data detection</ListItem>
        <ListItem>Data discovery</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Permissions and Policies" />
      <InfoText>
        For detection and discovery, Fides requires an IAM user with read-only
        DynamoDB permissions in order to detect, discover, and classify
        sensitive data. The AWS-managed{" "}
        <Code>AmazonDynamoDBReadOnlyAccess</Code> policy can be used to assign
        these permissions. If you intend to automate governance for DSR or
        Consent, Fides requires an IAM user with read-and-write DynamoDB
        permissions. The AWS-managed
        <Code>AmazonDynamoDBFullAccess</Code> policy can be used to assign these
        permissions. An IAM administrator can create the necessary principal for
        Fides using the AWS IAM guides, and assign the appropriate permissions
        policy to the IAM user.
      </InfoText>
      <InfoText>
        The permissions allow Fides to read the schema of, and data stored in,
        DynamoDB tables. This data is inspected only for the purpose of
        detecting sensitive data risks and no data is stored by Fides. As part
        of DSR or Consent orchestration, Fides will only write restricted
        updates to the tables specified by your Fides policy configuration.
      </InfoText>
      <InfoHeading text="Policy List" />
      <InfoText>
        The following AWS-managed policies provide the necessary permissions for
        Fides:
      </InfoText>
      <InfoUnorderedList>
        <ListItem>AmazonDynamoDBReadOnlyAccess</ListItem>
        <ListItem>
          AmazonDynamoDBFullAccess (only needed if automating governance for DSR
          or Consent)
        </ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const IAM_GUIDE_URL =
  "https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started.html#getting-started-iam-user";

const DYNAMO_PERMISSIONS = [
  {
    permission: "AmazonDynamoDBReadOnlyAccess",
    description:
      "Provides read-only access to Amazon DynamoDB via the AWS Management Console.",
  },
  {
    permission: "AmazonDynamoDBFullAccess",
    description:
      "Provides full access to Amazon DynamoDB via the AWS Management Console. Only needed if automating governance for DSR or Consent.",
  },
];

export const DynamoInstructions = () => (
  <>
    <InfoHeading text="Configuring a Fides -> DynamoDB Integration" />
    <InfoHeading text="Step 1: Create an IAM user in AWS" />
    <InfoText>
      Create an IAM user for Fides&apos; DynamoDB access following the{" "}
      <InfoLink href={IAM_GUIDE_URL}>AWS IAM user guide</InfoLink>.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Step 2: Assign policies to the IAM user" />
      <InfoText>
        Grant the necessary permissions to the IAM user by attaching directly
        the appropriate AWS-managed policy for your use case:
      </InfoText>
      <InfoPermissionsTable data={DYNAMO_PERMISSIONS} />
      <InfoHeading text="Step 3: Create an access key for the IAM user" />
      <InfoOrderedList>
        <ListItem>
          Create an access key for the IAM user under{" "}
          <strong>Security credentials</strong>
        </ListItem>
        <ListItem>Select the Other use case</ListItem>
        <ListItem>Copy the Access Key ID and Secret Access Key</ListItem>
      </InfoOrderedList>
      <InfoHeading text="Use the Credentials to Authenticate Your Integration" />
      <InfoText>
        Provide the credentials to your Fides instance to securely connect
        Fides.
      </InfoText>
    </ShowMoreContent>
  </>
);

const DYNAMO_TYPE_INFO = {
  placeholder: DYNAMO_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <DynamoOverview />,
  instructions: <DynamoInstructions />,
  tags: DYNAMO_TAGS,
};

export default DYNAMO_TYPE_INFO;
