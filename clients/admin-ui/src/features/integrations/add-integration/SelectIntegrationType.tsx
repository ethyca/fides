import { AntButton, Flex, Spacer, TabList, Tabs } from "fidesui";

import { FidesTab } from "~/features/common/DataTabs";
import FidesSpinner from "~/features/common/FidesSpinner";
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
  const { tabIndex, onChangeFilter, isFiltering, filteredTypes, tabs } =
    useIntegrationFilterTabs(INTEGRATION_TYPE_LIST);

  return (
    <>
      <Tabs index={tabIndex} onChange={onChangeFilter} mb={4}>
        <TabList>
          {tabs.map((label) => (
            <FidesTab label={label} key={label} />
          ))}
        </TabList>
      </Tabs>
      {isFiltering ? (
        <FidesSpinner />
      ) : (
        <Flex direction="column">
          {filteredTypes.map((i) => (
            <IntegrationBox
              integration={i.placeholder}
              key={i.placeholder.key}
              onConfigureClick={() => onConfigureClick(i)}
              otherButtons={
                <AntButton onClick={() => onDetailClick(i)}>Details</AntButton>
              }
            />
          ))}
        </Flex>
      )}
      <Flex>
        <Spacer />
        <AntButton onClick={onCancel}>Cancel</AntButton>
      </Flex>
    </>
  );
};

export default SelectIntegrationType;
