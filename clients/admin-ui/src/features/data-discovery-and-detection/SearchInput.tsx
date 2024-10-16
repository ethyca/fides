import { AntButton as Button, AntInput, AntSpace } from "fidesui";
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
    <AntSpace.Compact>
      <AntInput
        value={currentInput}
        placeholder="Search..."
        onChange={handleOnChange}
        className="w-full"
      />
      <Button onClick={onClear} className="bg-[#f5f5f5] hover:!bg-[#d9d9d9]">
        Clear
      </Button>
    </AntSpace.Compact>
  );
};
