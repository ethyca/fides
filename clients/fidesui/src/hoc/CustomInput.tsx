import { Input, InputProps, InputRef } from "antd/lib";
import { debounce } from "lodash";
import React, { useEffect, useMemo, useState } from "react";

export interface CustomInputProps extends InputProps {
  /**
   * Optional debounce delay
   * - number: debounce delay in milliseconds
   * - true: use default delay of 500ms
   * - false/undefined: no debouncing
   */
  debounce?: number | boolean;
}

const DEFAULT_DEBOUNCE_DELAY = 500;

/**
 * Higher-order component that adds consistent styling and enhanced functionality to Ant Design's Input component.
 *
 * Features:
 * - Optional debouncing support via the debounce prop
 * - Maintains instant UI feedback while debouncing onChange events
 * - Proper cleanup to prevent memory leaks
 *
 * @example
 * ```tsx
 * // No debouncing (standard behavior)
 * <CustomInput value={value} onChange={handleChange} />
 *
 * // With default 500ms debounce
 * <CustomInput debounce value={value} onChange={handleChange} />
 *
 * // With custom debounce delay
 * <CustomInput debounce={300} value={value} onChange={handleChange} />
 * ```
 */
const withCustomProps = (WrappedComponent: typeof Input) => {
  const WrappedInput = React.forwardRef<InputRef, CustomInputProps>(
    ({ debounce: debounceProp, value, onChange, ...props }, ref) => {
      // Determine the actual delay: true -> 500ms, number -> that number, false/undefined -> 0
      let debounceDelay = 0;
      if (debounceProp === true) {
        debounceDelay = DEFAULT_DEBOUNCE_DELAY;
      } else if (typeof debounceProp === "number") {
        debounceDelay = debounceProp;
      }

      // Only use internal state when debouncing
      const [internalValue, setInternalValue] = useState(value ?? "");

      // Create debounced handler only when debounce is enabled
      const debouncedOnChange = useMemo(
        () =>
          debounceDelay && onChange
            ? debounce(onChange, debounceDelay)
            : undefined,
        [onChange, debounceDelay],
      );

      // Sync internal state with external value when debouncing
      useEffect(() => {
        if (debounceDelay) {
          setInternalValue(value ?? "");
        }
      }, [value, debounceDelay]);

      // Cleanup on unmount
      useEffect(() => {
        return () => debouncedOnChange?.cancel();
      }, []);

      // Determine which value and handler to use based on debounce
      const inputValue = debounceDelay ? internalValue : value;
      const inputOnChange =
        debounceDelay && debouncedOnChange
          ? (e: React.ChangeEvent<HTMLInputElement>) => {
              setInternalValue(e.target.value);
              debouncedOnChange(e);
            }
          : onChange;

      return (
        <WrappedComponent
          ref={ref}
          {...props}
          value={inputValue}
          onChange={inputOnChange}
        />
      );
    },
  );
  return WrappedInput;
};

const CustomInputBase = withCustomProps(Input);

// Create a type that includes the sub-components
type CustomInputType = typeof CustomInputBase & {
  TextArea: typeof Input.TextArea;
  Password: typeof Input.Password;
  Search: typeof Input.Search;
};

// Attach the sub-components from the original Input
export const CustomInput = CustomInputBase as CustomInputType;
CustomInput.TextArea = Input.TextArea;
CustomInput.Password = Input.Password;
CustomInput.Search = Input.Search;
