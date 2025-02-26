import { Flex, Text } from "fidesui";

import Toggle from "../Toggle";

interface ConsentChildItemProps {
  id: string;
  title: string;
  value: boolean;
  onChange: (value: boolean) => void;
  isDisabled?: boolean;
}
const ConsentChildItem = ({
  id,
  title,
  value,
  onChange,
  isDisabled,
}: ConsentChildItemProps) => (
  <Flex justifyContent="space-between" alignItems="center" pl={0} py={1}>
    <Text fontSize={16}>{title}</Text>
    <Toggle
      label={title}
      name={id}
      id={id}
      disabled={isDisabled}
      checked={value}
      onChange={() => onChange(!value)}
    />
  </Flex>
);
export default ConsentChildItem;
