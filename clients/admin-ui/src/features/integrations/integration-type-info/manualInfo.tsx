import { InfoHeading, InfoText } from "~/features/common/copy/components";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";
import { AccessLevel, ConnectionType } from "~/types/api";

export const MANUAL_PLACEHOLDER = {
  name: "Manual Tasks",
  key: "manual_placeholder",
  connection_type: ConnectionType.MANUAL_TASK,
  access: AccessLevel.READ,
  created_at: "",
};

const ManualOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Manual Integrations enable you to create and assign tasks for data that
      requires manual handling during access and erasure requests. Tasks can be
      assigned to internal users within Fides or external users who complete
      them securely through the external task portal.
    </InfoText>
    <InfoText>
      When privacy requests involve manual integrations, execution will pause in
      a <em>Requires input</em> state until all assigned tasks are completed.
    </InfoText>
  </>
);

const MANUAL_TAGS = ["DSR", "Manual tasks"];

const MANUAL_TYPE_INFO = {
  placeholder: MANUAL_PLACEHOLDER,
  category: ConnectionCategory.MANUAL,
  tags: MANUAL_TAGS,
  overview: <ManualOverview />,
  enabledFeatures: [
    IntegrationFeatureEnum.TASKS,
    IntegrationFeatureEnum.WITHOUT_CONNECTION,
  ],
};

export default MANUAL_TYPE_INFO;
