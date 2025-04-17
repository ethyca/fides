import { debounce } from "lodash";
import { useCallback, useState } from "react";

import SearchInput, { SearchInputProps } from "~/features/common/SearchInput";

export const DebouncedSearchInput = ({
  value,
  onChange,
  placeholder,
  ...props
}: SearchInputProps) => {
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
    <SearchInput
      value={currentInput}
      onChange={handleOnChange}
      onClear={onClear}
      placeholder={placeholder}
      {...props}
    />
  );
};
