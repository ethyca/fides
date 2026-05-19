import { useStateBinding } from "@json-render/react";
import { Form, isoCodesToOptions, LocationSelect } from "fidesui";
import React from "react";

import {
  BaseFieldProps,
  FieldWrapper,
  useDefaultValueSeed,
} from "./fieldUtils";

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
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
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
    </FieldWrapper>
  );
};
