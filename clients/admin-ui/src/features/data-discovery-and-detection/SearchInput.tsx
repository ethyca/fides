import { debounce } from "lodash";
import { useCallback, useState } from "react";

import SearchBar from "~/features/common/SearchBar";

interface SearchInputProps {
  value: string;
  onChange: (newValue: string) => void;
}

export const SearchInput = ({ value, onChange }: SearchInputProps) => {
  const INPUT_CHANGE_DELAY = 500;
  const [currentInput, setCurrentInput] = useState(value);

  // Add some delay to prevent fetching on each key pressed while typing
  const debouncedOnChange = debounce(onChange, INPUT_CHANGE_DELAY);

  const handleOnChange = useCallback(
    (newValue: string) => {
      setCurrentInput(newValue);
      debouncedOnChange(newValue);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const onClear = () => {
    setCurrentInput("");
    onChange("");
  };

  return (
    <SearchBar
      search={currentInput}
      onChange={handleOnChange}
      onClear={onClear}
    />
  );
};
