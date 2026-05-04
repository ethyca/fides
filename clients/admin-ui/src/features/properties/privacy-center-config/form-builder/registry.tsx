import { defineRegistry, useStateBinding } from "@json-render/react";
import { Form, Input, Radio, Select } from "fidesui";
import React from "react";

import { catalog } from "./catalog";

interface BaseFieldProps {
  name: string;
  label: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
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

// Each field binds its current value to /form/<name> in the json-render
// state model. In Preview mode this lets visibility conditions react to
// user input (e.g. show field B when /form/country eq "US"). In Edit mode
// each field has its own isolated provider, so the binding is harmless.
const useFieldBinding = <T,>(name: string) =>
  useStateBinding<T>(`/form/${name}`);

const TextField = ({ props }: { props: BaseFieldProps }) => {
  const [value, setValue] = useFieldBinding<string>(props.name);
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label={props.label} required={props.required}>
        <Input
          aria-label={props.label}
          data-testid={`field-${props.name}`}
          placeholder={props.placeholder}
          value={value ?? ""}
          onChange={(e) => setValue(e.target.value)}
        />
      </Form.Item>
    </FieldWrapper>
  );
};

const SelectField = ({ props }: { props: BaseFieldProps }) => {
  const [value, setValue] = useFieldBinding<string>(props.name);
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label={props.label} required={props.required}>
        <Select
          aria-label={props.label}
          data-testid={`field-${props.name}`}
          placeholder={props.placeholder}
          value={value}
          onChange={(v) => setValue(v)}
          options={(props.options ?? []).map((o) => ({ label: o, value: o }))}
        />
      </Form.Item>
    </FieldWrapper>
  );
};

const MultiSelectField = ({ props }: { props: BaseFieldProps }) => {
  const [value, setValue] = useFieldBinding<string[]>(props.name);
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label={props.label} required={props.required}>
        <Select
          aria-label={props.label}
          mode="multiple"
          data-testid={`field-${props.name}`}
          placeholder={props.placeholder}
          value={value ?? []}
          onChange={(v) => setValue(v)}
          options={(props.options ?? []).map((o) => ({ label: o, value: o }))}
        />
      </Form.Item>
    </FieldWrapper>
  );
};

const RadioField = ({ props }: { props: BaseFieldProps }) => {
  const [value, setValue] = useFieldBinding<string>(props.name);
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label={props.label} required={props.required}>
        <Radio.Group
          aria-label={props.label}
          data-testid={`field-${props.name}`}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          options={(props.options ?? []).map((o) => ({ label: o, value: o }))}
        />
      </Form.Item>
    </FieldWrapper>
  );
};

const LOCATION_DEFAULT_OPTIONS = ["United States", "Canada", "United Kingdom"];

const LocationField = ({ props }: { props: BaseFieldProps }) => {
  // Empty array means "no custom options" — fall back to defaults so the
  // dropdown is never empty in the preview.
  const options =
    props.options && props.options.length > 0
      ? props.options
      : LOCATION_DEFAULT_OPTIONS;
  const [value, setValue] = useFieldBinding<string>(props.name);
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label={props.label} required={props.required}>
        <Select
          aria-label={props.label}
          data-testid={`field-${props.name}`}
          placeholder={props.placeholder}
          value={value}
          onChange={(v) => setValue(v)}
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
    Radio: ({ props }) => <RadioField props={props as BaseFieldProps} />,
    Location: ({ props }) => <LocationField props={props as BaseFieldProps} />,
  },
});
