import { Button, Input, InputGroup, InputRightAddon } from "fidesui";
import { debounce } from "lodash";
import { ChangeEventHandler, useCallback, useState } from "react";

interface SearchInputProps {
  value: string;
  onChange: (newValue: string) => void;
}

export const SearchInput = ({ value, onChange }: SearchInputProps) => {
  const INPUT_CHANGE_DELAY = 500;
  const [currentInput, setCurrentInput] = useState(value);

  // Add some delay to prevent fetching on each key pressed while typing
  const debouncedOnChange = debounce(onChange, INPUT_CHANGE_DELAY);

  const handleOnChange: ChangeEventHandler<HTMLInputElement> = useCallback(
    (e) => {
      setCurrentInput(e.currentTarget.value);
      debouncedOnChange(e.currentTarget.value);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const onClear = () => {
    setCurrentInput("");
    onChange("");
  };

  return (
    <InputGroup size="xs" w="full">
      <Input
        size="xs"
        placeholder="Search..."
        value={currentInput}
        onChange={handleOnChange}
        w="full"
      />
      <InputRightAddon px={0}>
        <Button size="xs" fontWeight="normal" onClick={onClear}>
          Clear
        </Button>
      </InputRightAddon>
    </InputGroup>
  );
};
