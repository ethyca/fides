import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { AccessLevel } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";
import { ConnectionType } from "~/types/api/models/ConnectionType";
import { IntegrationFeature } from "~/types/api/models/IntegrationFeature";

export const AWS_INTEGRATION_PLACEHOLDER = {
  name: "Amazon Web Services",
  key: "aws_placeholder",
  connection_type: ConnectionType.AWS,
  access: AccessLevel.READ,
  created_at: "",
};

export const AWS_DESCRIPTION = (
  <>
    Amazon Web Services (AWS) cloud infrastructure integration allows you to
    discover and monitor your AWS resources. Adding AWS as an integration
    enables automated scanning of your cloud environment for better visibility
    and control.
  </>
);

export const AWS_AUTH_DESCRIPTION =
  "AWS integration supports both IAM access key authentication and automatic credential discovery (e.g. instance profiles, environment variables). You may optionally provide a role ARN to assume for cross-account access.";

const AWSIntegrationOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>{AWS_DESCRIPTION}</InfoText>
    <InfoText>
      <strong>Authentication:</strong> {AWS_AUTH_DESCRIPTION}
    </InfoText>
  </>
);

const AWS_TAGS = ["Detection", "Inventory"];

const AWS_INTEGRATION_TYPE_INFO = {
  placeholder: AWS_INTEGRATION_PLACEHOLDER,
  category: ConnectionCategory.CLOUD_INFRASTRUCTURE,
  tags: AWS_TAGS,
  overview: <AWSIntegrationOverview />,
  description: AWS_DESCRIPTION,
  enabledFeatures: [IntegrationFeature.DATA_DISCOVERY],
};

export default AWS_INTEGRATION_TYPE_INFO;
