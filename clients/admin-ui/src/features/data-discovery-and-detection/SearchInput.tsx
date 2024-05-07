import { Button, Input, InputGroup, InputRightAddon } from "@fidesui/react";
import { debounce } from "lodash";
import { ChangeEventHandler, useCallback, useEffect, useState } from "react";

interface SearchInputProps {
  value: string;
  onChange: (newValue: string) => void;
}

const SearchInput: React.FC<SearchInputProps> = ({ value, onChange }) => {
  const INPUT_CHANGE_DELAY = 500;
  const [currentInput, setCurrentInput] = useState(value);

  // Add some delay to prevent fetching on each key pressed while typing
  const debouncedOnChange = debounce(onChange, INPUT_CHANGE_DELAY);

  const handleOnChange: ChangeEventHandler<HTMLInputElement> = useCallback(
    (e) => {
      setCurrentInput(e.currentTarget.value);
      debouncedOnChange(e.currentTarget.value);
    },
    []
  );

  const onClear = () => {
    setCurrentInput("");
    onChange("");
  };

  return (
    <InputGroup size="xs">
      <Input
        size="xs"
        placeholder="Search..."
        value={currentInput}
        onChange={handleOnChange}
      />
      <InputRightAddon>
        <Button size="xs" fontWeight="normal" onClick={onClear}>
          Clear
        </Button>
      </InputRightAddon>
    </InputGroup>
  );
};
export default SearchInput;
