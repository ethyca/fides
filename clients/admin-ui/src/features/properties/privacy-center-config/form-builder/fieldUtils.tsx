import React, { useEffect, useRef } from "react";

export interface IdentityFieldProps {
  required: boolean;
  "data-element-id"?: string;
}

export interface BaseFieldProps {
  name: string;
  label: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
  default_value?: string | string[];
  "data-element-id"?: string;
}

export const isEmptyValue = (v: unknown) =>
  v === undefined ||
  v === null ||
  v === "" ||
  (Array.isArray(v) && v.length === 0);

export const stableValueKey = (v: unknown) => JSON.stringify(v ?? null);

export const FieldWrapper = ({
  elementId,
  children,
}: {
  elementId?: string;
  children: React.ReactNode;
}) => {
  if (!elementId) {
    // eslint-disable-next-line react/jsx-no-useless-fragment
    return <>{children}</>;
  }
  return <span data-element-id={elementId}>{children}</span>;
};

/**
 * Seed the field's binding from `default_value`:
 * - On first mount when nothing is in state yet.
 * - When the author changes `default_value` in the properties panel and the
 *   field is either empty or still showing the previous default. This keeps
 *   the Edit-mode preview in sync with the property the author just edited.
 *
 * If the end user has typed something different, we leave their value alone.
 */
export const useDefaultValueSeed = <T,>(
  value: T | undefined,
  setValue: (next: T) => void,
  defaultValue: T | undefined,
) => {
  const previousDefaultRef = useRef<T | undefined>(defaultValue);
  useEffect(() => {
    const hasDefault = !isEmptyValue(defaultValue);
    if (!hasDefault) {
      previousDefaultRef.current = defaultValue;
      return;
    }
    const matchesPreviousDefault =
      stableValueKey(value) === stableValueKey(previousDefaultRef.current);
    if (isEmptyValue(value) || matchesPreviousDefault) {
      setValue(defaultValue as T);
    }
    previousDefaultRef.current = defaultValue;
    // setValue is stable (state-binding setter). Re-running on every value
    // change would clobber user input — we intentionally trigger only on
    // defaultValue changes plus the initial mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stableValueKey(defaultValue)]);
};
