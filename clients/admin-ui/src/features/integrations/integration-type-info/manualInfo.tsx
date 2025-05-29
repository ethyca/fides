import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";
import { AccessLevel, ConnectionType } from "~/types/api";

export const MANUAL_PLACEHOLDER = {
  name: "Manual",
  key: "manual_placeholder",
  connection_type: ConnectionType.MANUAL_WEBHOOK,
  access: AccessLevel.READ,
  created_at: "",
};

const ManualOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Manual integrations allow you to manually configure and manage data
      connections that don&apos;t have automated connectors. This option
      provides flexibility for custom data sources or systems that require
      manual configuration and monitoring.
    </InfoText>
  </>
);

const MANUAL_TAGS = ["DSR", "Manual tasks"];

const MANUAL_TYPE_INFO = {
  placeholder: MANUAL_PLACEHOLDER,
  category: ConnectionCategory.OTHER,
  tags: MANUAL_TAGS,
  overview: <ManualOverview />,
  enabledFeatures: [
    IntegrationFeatureEnum.TASKS,
    IntegrationFeatureEnum.WITHOUT_CONNECTION,
  ],
};

export default MANUAL_TYPE_INFO;
