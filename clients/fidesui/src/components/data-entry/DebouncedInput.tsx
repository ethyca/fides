import { AntInput as Input, AntInputProps as InputProps } from "fidesui";
import { debounce } from "lodash";
import { useCallback, useEffect, useRef, useState } from "react";

export interface DebouncedInputProps extends InputProps {
  /**
   * Debounce delay in milliseconds
   * @default 500
   */
  delay?: number;
}

/**
 * A debounced version of AntInput that delays onChange events.
 * Useful for filtering/search inputs where you want to avoid triggering
 * API calls or expensive operations on every keystroke.
 *
 * @example
 * ```tsx
 * <DebouncedInput
 *   placeholder="Search..."
 *   value={searchValue}
 *   onChange={(e) => setSearchValue(e.target.value)}
 *   delay={500}
 * />
 * ```
 */
export const DebouncedInput = ({
  value,
  onChange,
  delay = 500,
  ...props
}: DebouncedInputProps) => {
  const [currentInput, setCurrentInput] = useState(value || "");
  const debouncedOnChangeRef = useRef(debounce(onChange || (() => {}), delay));

  // Keep internal state in sync with external value prop
  useEffect(() => {
    setCurrentInput(value || "");
  }, [value]);

  // Update debounce delay if it changes
  useEffect(() => {
    debouncedOnChangeRef.current = debounce(onChange || (() => {}), delay);
  }, [onChange, delay]);

  const handleOnChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setCurrentInput(newValue);
      debouncedOnChangeRef.current(e);
    },
    [],
  );

  return <Input {...props} value={currentInput} onChange={handleOnChange} />;
};
