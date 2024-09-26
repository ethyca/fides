import { AntSwitch as Switch, Flex, FormLabel } from "fidesui";

import QuestionTooltip from "~/features/common/QuestionTooltip";

const RegulatedToggle = ({
  id,
  isChecked,
  onChange,
}: {
  id: string;
  isChecked: boolean;
  onChange: () => void;
}) => (
  <Flex alignItems="center" gap="8px">
    <Switch
      checked={isChecked}
      size="small"
      onChange={onChange}
      id={id}
      data-testid="regulated-toggle"
    />
    <FormLabel fontSize="sm" m={0} htmlFor={id}>
      Regulated
    </FormLabel>
    <QuestionTooltip label="Toggle on to see only locations in this region with privacy regulations supported by Fides" />
  </Flex>
);

export default RegulatedToggle;
