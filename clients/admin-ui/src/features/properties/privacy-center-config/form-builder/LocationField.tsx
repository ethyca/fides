import { useStateBinding } from "@json-render/react";
import { Form, isoCodesToOptions, LocationSelect } from "fidesui";
import React, { useEffect, useRef } from "react";

interface BaseFieldProps {
  name: string;
  label: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
  default_value?: string | string[];
  "data-element-id"?: string;
}

const isEmptyValue = (v: unknown) =>
  v === undefined ||
  v === null ||
  v === "" ||
  (Array.isArray(v) && v.length === 0);

const stableValueKey = (v: unknown) => JSON.stringify(v ?? null);

const useDefaultValueSeed = <T,>(
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stableValueKey(defaultValue)]);
};

export const LocationField = ({ props }: { props: BaseFieldProps }) => {
  // Custom options (when provided) are treated as ISO 3166-1/2 codes — the
  // same shape Privacy Center expects. With none configured, LocationSelect
  // falls back to its full ISO list.
  const isoOptions =
    props.options && props.options.length > 0
      ? isoCodesToOptions(props.options)
      : undefined;
  const [value, setValue] = useStateBinding<string>(`/form/${props.name}`);
  useDefaultValueSeed(
    value,
    setValue,
    props.default_value as string | undefined,
  );
  const elementId = props["data-element-id"];
  const content = (
    <Form.Item label={props.label} required={props.required}>
      <LocationSelect
        aria-label={props.label}
        data-testid={`field-${props.name}`}
        placeholder={props.placeholder}
        value={value}
        onChange={(v) => setValue(v)}
        onBlur={() => {}}
        options={isoOptions}
      />
    </Form.Item>
  );
  if (!elementId) {
    return content;
  }
  return <span data-element-id={elementId}>{content}</span>;
};
