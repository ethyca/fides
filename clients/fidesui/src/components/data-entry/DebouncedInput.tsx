import { Input, InputProps } from "antd/lib";
import { debounce } from "lodash";
import { useEffect, useMemo, useState } from "react";

export interface DebouncedInputProps extends InputProps {
  /**
   * Debounce delay in milliseconds
   * @default 500
   */
  delay?: number;
}

/**
 * A debounced version of AntInput that delays onChange events.
 * The UI updates immediately while the onChange callback is debounced.
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
  const [internalValue, setInternalValue] = useState(value || "");

  // Keep internal state in sync with external value prop
  useEffect(() => {
    setInternalValue(value || "");
  }, [value]);

  // Create a memoized debounced onChange handler
  // Create a memoized debounced onChange handler
  const debouncedOnChange = useMemo(
    () => (onChange ? debounce(onChange, delay) : undefined),
    [onChange, delay],
  );

  // Cleanup on unmount or when dependencies change
  useEffect(() => {
    return () => {
      debouncedOnChange?.cancel();
    };
  }, [debouncedOnChange]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Update internal state immediately for instant UI feedback
    setInternalValue(e.target.value);
    // Call debounced onChange
    debouncedOnChange?.(e);
  };

  return <Input {...props} value={internalValue} onChange={handleChange} />;
};
