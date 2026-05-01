import { defineRegistry } from "@json-render/react";
import { Form, Input, Select } from "fidesui";
import React from "react";

import { catalog } from "./catalog";

interface BaseFieldProps {
  name: string;
  label: string;
  required: boolean;
  options?: string[];
  "data-element-id"?: string;
}

const FormContainer = ({ children }: { children?: React.ReactNode }) => (
  <Form layout="vertical">{children}</Form>
);

const FieldWrapper = ({
  elementId,
  children,
}: {
  elementId?: string;
  children: React.ReactNode;
}) => {
  if (!elementId) {
    return children as React.ReactElement;
  }
  return <span data-element-id={elementId}>{children}</span>;
};

const TextField = ({ props }: { props: BaseFieldProps }) => (
  <FieldWrapper elementId={props["data-element-id"]}>
    <Form.Item label={props.label} required={props.required}>
      <Input aria-label={props.label} data-testid={`field-${props.name}`} />
    </Form.Item>
  </FieldWrapper>
);

const SelectField = ({ props }: { props: BaseFieldProps }) => (
  <FieldWrapper elementId={props["data-element-id"]}>
    <Form.Item label={props.label} required={props.required}>
      <Select
        aria-label={props.label}
        data-testid={`field-${props.name}`}
        options={(props.options ?? []).map((o) => ({ label: o, value: o }))}
      />
    </Form.Item>
  </FieldWrapper>
);

const MultiSelectField = ({ props }: { props: BaseFieldProps }) => (
  <FieldWrapper elementId={props["data-element-id"]}>
    <Form.Item label={props.label} required={props.required}>
      <Select
        aria-label={props.label}
        mode="multiple"
        data-testid={`field-${props.name}`}
        options={(props.options ?? []).map((o) => ({ label: o, value: o }))}
      />
    </Form.Item>
  </FieldWrapper>
);

const LOCATION_DEFAULT_OPTIONS = ["United States", "Canada", "United Kingdom"];

const LocationField = ({ props }: { props: BaseFieldProps }) => {
  // Empty array means "no custom options" — fall back to defaults so the
  // dropdown is never empty in the preview.
  const options =
    props.options && props.options.length > 0
      ? props.options
      : LOCATION_DEFAULT_OPTIONS;
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label={props.label} required={props.required}>
        <Select
          aria-label={props.label}
          data-testid={`field-${props.name}`}
          options={options.map((o) => ({ label: o, value: o }))}
        />
      </Form.Item>
    </FieldWrapper>
  );
};

export const { registry } = defineRegistry(catalog.jsonRender, {
  components: {
    Form: ({ children }) => <FormContainer>{children}</FormContainer>,
    Text: ({ props }) => <TextField props={props as BaseFieldProps} />,
    Select: ({ props }) => <SelectField props={props as BaseFieldProps} />,
    MultiSelect: ({ props }) => (
      <MultiSelectField props={props as BaseFieldProps} />
    ),
    Location: ({ props }) => <LocationField props={props as BaseFieldProps} />,
  },
});
