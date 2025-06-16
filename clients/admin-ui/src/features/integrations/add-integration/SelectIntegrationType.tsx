import { AntButton as Button, AntSpin, AntTabs, Flex, Spacer } from "fidesui";

import { useFlags } from "~/features/common/features";
import {
  INTEGRATION_TYPE_LIST,
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import useIntegrationFilterTabs from "~/features/integrations/useIntegrationFilterTabs";

type Props = {
  onCancel: () => void;
  onDetailClick: (type: IntegrationTypeInfo) => void;
  onConfigureClick: (type: IntegrationTypeInfo) => void;
};

const SelectIntegrationType = ({
  onCancel,
  onDetailClick,
  onConfigureClick,
}: Props) => {
  const {
    activeKey,
    onChangeFilter,
    isUpdatingFilter,
    filteredTypes,
    tabItems,
  } = useIntegrationFilterTabs({
    integrationTypes: INTEGRATION_TYPE_LIST,
  });

  const {
    flags: { oktaMonitor, alphaNewManualIntegration },
  } = useFlags();

  return (
    <>
      <AntTabs
        activeKey={activeKey}
        onChange={onChangeFilter}
        items={tabItems}
        className="mb-4"
      />
      {isUpdatingFilter ? (
        <AntSpin
          size="large"
          className="my-24 flex h-full items-center justify-center"
        />
      ) : (
        <Flex direction="column">
          {filteredTypes.map((i) => {
            if (!oktaMonitor && i.placeholder.connection_type === "okta") {
              return null;
            }
            // DEFER (ENG-675): Remove this once the alpha feature is released
            if (
              !alphaNewManualIntegration &&
              i.placeholder.connection_type === "manual_webhook"
            ) {
              return null;
            }

            return (
              <IntegrationBox
                integration={i.placeholder}
                key={i.placeholder.key}
                onConfigureClick={() => onConfigureClick(i)}
                otherButtons={
                  <Button onClick={() => onDetailClick(i)}>Details</Button>
                }
              />
            );
          })}
        </Flex>
      )}
      <Flex>
        <Spacer />
        <Button onClick={onCancel}>Cancel</Button>
      </Flex>
    </>
  );
};

export default SelectIntegrationType;
