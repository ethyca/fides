import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { AccessLevel } from "~/types/api";
import { ConnectionCategory } from "~/types/api/models/ConnectionCategory";
import { ConnectionType } from "~/types/api/models/ConnectionType";
import { IntegrationFeature } from "~/types/api/models/IntegrationFeature";

export const AWS_INTEGRATION_PLACEHOLDER = {
  name: "AWS",
  key: "aws_placeholder",
  connection_type: ConnectionType.AWS,
  access: AccessLevel.READ,
  created_at: "",
};

export const AWS_DESCRIPTION = (
  <>
    AWS Cloud Infrastructure monitoring scans your AWS account to discover which
    services are in use across your environment. Detected resources are surfaced
    for review and can be promoted to your Fides data map as Systems.
  </>
);

const AWSIntegrationOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>{AWS_DESCRIPTION}</InfoText>
    <InfoHeading text="Authentication" />
    <InfoText>
      Supports IAM access key credentials or automatic authentication via
      instance role / ECS task role. An optional assume-role ARN can be provided
      for cross-account access.
    </InfoText>
    <InfoHeading text="Prerequisites" />
    <InfoText>
      AWS Resource Explorer must be enabled in your account. To scan all regions
      without specifying them individually, an aggregator index must be
      configured in Resource Explorer.
    </InfoText>
  </>
);

const AWS_TAGS = ["Discovery", "Inventory"];

const AWS_INTEGRATION_TYPE_INFO = {
  placeholder: AWS_INTEGRATION_PLACEHOLDER,
  category: ConnectionCategory.CLOUD_PROVIDER,
  tags: AWS_TAGS,
  overview: <AWSIntegrationOverview />,
  description: AWS_DESCRIPTION,
  enabledFeatures: [IntegrationFeature.DATA_DISCOVERY],
};

export default AWS_INTEGRATION_TYPE_INFO;
