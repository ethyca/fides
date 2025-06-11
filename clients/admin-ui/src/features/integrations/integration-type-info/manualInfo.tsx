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
      A Manual Integration provides a simple way for data to be manually
      uploaded for access and erasure requests.
    </InfoText>
    <InfoText>
      If you have manual integrations defined, privacy request execution will
      exit early and remain in a state of <em>Requires Input</em>. Once data has
      been manually uploaded for all the manual integrations, then the privacy
      request can be resumed. Data uploaded for manual integrations is passed on
      directly to the data subject alongside the data package.
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
