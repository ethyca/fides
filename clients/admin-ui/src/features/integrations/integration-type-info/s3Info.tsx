import { ListItem } from "fidesui";

import {
  InfoCodeBlock,
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

export const S3_PLACEHOLDER = {
  name: "Amazon S3",
  key: "s3_placeholder",
  connection_type: ConnectionType.S3,
  access: AccessLevel.READ,
  created_at: "",
};

export const S3_TAGS = ["Data Warehouse", "S3", "Detection", "Discovery"];

export const S3Overview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Continuously monitor S3 to detect and track schema-level changes,
      automatically discover and label data categories as well as automatically
      process DSR (privacy requests) and consent enforcement to proactively
      manage data governance risks.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>Object storage</ListItem>
        <ListItem>Storage system</ListItem>
        <ListItem>Cloud provider</ListItem>
        <ListItem>Data detection</ListItem>
        <ListItem>Data discovery</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Permissions" />
      <InfoText>
        Fides requires an IAM principal with read-only S3 permissions in order
        to detect, discover, and classify sensitive data. The AWS-managed
        AmazonS3ReadOnlyAccess policy can be used to assign these permissions.
        An IAM administrator can create the necessary principal for Fides using
        the AWS IAM guides, and assign the appropriate permissions policy to the
        IAM principal.
      </InfoText>
      <InfoText>
        The permissions allow Fides to list buckets and read object data data
        stored in those buckets. This data is inspected only for the purpose of
        detecting sensitive data risks and no data is stored by Fides.
      </InfoText>
      <InfoText>
        Ethyca recommends creating an IAM role with the appropriate permissions,
        which will be assumed by Fides at runtime, with ephemeral credentials.
        There must also be an IAM user with fixed credentials that Fides uses
        strictly for assuming the IAM role with the appropriate permissions. If
        desired, Fides also supports authenticating directly as an IAM user with
        the appropriate permissions, but this is considered a less secure
        option.
      </InfoText>
      <InfoHeading text="Permissions list" />
      <InfoUnorderedList>
        <ListItem>AmazonS3ReadOnlyAccess</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const IAM_GUIDE_URL =
  "https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started.html#getting-started-iam-user";

const SAMPLE_JSON = `{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": "sts:AssumeRole",
			"Resource": "arn:aws:iam::[AWS ACCOUNT NUMBER]:role/[Fides S3 Access Role ARN]"
		}
	]
}`;

export const S3Instructions = () => (
  <>
    <InfoHeading text="Configuring a Fides -> Amazon S3 Integration" />
    <InfoHeading text="Step 1: Create an IAM role in AWS" />
    <InfoText>
      Create an IAM role for Fides&apos; S3 access following the AWS IAM roles
      guide. This role will be referred to below as the Fides S3 Access Role.
    </InfoText>

    <ShowMoreContent>
      <InfoHeading text="Step 2: Assign policies to the IAM role" />
      <InfoText>
        Grant the necessary permissions to the IAM role by attaching the
        following AWS-managed policy:
      </InfoText>
      <InfoPermissionsTable
        data={[
          {
            permission: "AmazonS3ReadOnlyAccess",
            description:
              "Provides read-only access to all buckets via the AWS Management Console.",
          },
        ]}
      />
      <InfoHeading text="Step 3: Create an IAM user for assuming a role" />
      <InfoText>
        Follow the <InfoLink href={IAM_GUIDE_URL}>AWS guide</InfoLink> for
        creating an IAM user to create an IAM user that Fides will authenticate
        as in order to assume the Fides S3 Access Role created above, and
        retrieve ephemeral credentials.
      </InfoText>
      <InfoHeading text="Step 4: Grant the IAM user permission to assume the Fides S3 Access Role" />
      <InfoText>
        Navigate to the IAM user’s Permissions page and add a permission by
        creating an inline policy. This permission should grant the IAM user
        permission to assume the Fides S3 Access Role created above (you’ll need
        to retrieve the role ARN). The inline policy should look similar to
        this:
      </InfoText>
      <InfoCodeBlock>{SAMPLE_JSON}</InfoCodeBlock>
      <InfoHeading text="Step 5: Create an access key for the IAM user" />
      <InfoOrderedList>
        <ListItem>
          Create an access key for the IAM user under{" "}
          <strong>Security credentials</strong>.
        </ListItem>
        <ListItem>Select the Other use case</ListItem>
        <ListItem>Copy the Access Key ID and Secret Access Key</ListItem>
      </InfoOrderedList>
      <InfoHeading text="Step 6: Use the credentials to authenticate your integration" />
      <InfoText>
        Provide the credentials to your Fides instance to securely connect
        Fides. For the Assume Role ARN, provide the ARN for the Fides S3 Access
        Role created in step 1.{" "}
      </InfoText>
    </ShowMoreContent>
  </>
);

const S3_TYPE_INFO = {
  placeholder: S3_PLACEHOLDER,
  category: ConnectionCategory.DATA_WAREHOUSE,
  overview: <S3Overview />,
  instructions: <S3Instructions />,
  tags: S3_TAGS,
};

export default S3_TYPE_INFO;
