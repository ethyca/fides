import { Flex, Text, Checkbox } from "@fidesui/react";
import { useState, HTMLProps } from "react";

export const DefaultCell = ({ value }: { value: string }) => (
  <Flex alignItems="center" height="100%">
    <Text fontSize="xs" lineHeight={4} fontWeight="normal">
      {value}
    </Text>
  </Flex>
);

type IndeterminateCheckboxCellProps = {
  indeterminate?: boolean;
  initialValue?: boolean;
} & HTMLProps<HTMLInputElement>;

export const IndeterminateCheckboxCell = ({
  indeterminate,
  className = "",
  initialValue,
  ...rest
}: IndeterminateCheckboxCellProps) => {
  const [initialCheckBoxValue] = useState(initialValue);

  return (
    <Flex alignItems="center" justifyContent="center">
      <Checkbox
        isChecked={initialCheckBoxValue || rest.checked}
        isDisabled={initialCheckBoxValue}
        onChange={rest.onChange}
        isIndeterminate={!rest.checked && indeterminate}
        colorScheme="purple"
      />
    </Flex>
  );
};
