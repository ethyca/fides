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

const FormContainer: React.FC<{ children?: React.ReactNode }> = ({
  children,
}) => <Form layout="vertical">{children}</Form>;

const FieldWrapper: React.FC<{
  elementId?: string;
  children: React.ReactNode;
}> = ({ elementId, children }) => {
  if (!elementId) {
    return <>{children}</>;
  }
  return <span data-element-id={elementId}>{children}</span>;
};

const TextField: React.FC<{ props: BaseFieldProps }> = ({ props }) => (
  <FieldWrapper elementId={props["data-element-id"]}>
    <Form.Item label={props.label} required={props.required}>
      <Input data-testid={`field-${props.name}`} />
    </Form.Item>
  </FieldWrapper>
);

const SelectField: React.FC<{ props: BaseFieldProps }> = ({ props }) => (
  <FieldWrapper elementId={props["data-element-id"]}>
    <Form.Item label={props.label} required={props.required}>
      <Select
        data-testid={`field-${props.name}`}
        options={(props.options ?? []).map((o) => ({ label: o, value: o }))}
      />
    </Form.Item>
  </FieldWrapper>
);

const MultiSelectField: React.FC<{ props: BaseFieldProps }> = ({ props }) => (
  <FieldWrapper elementId={props["data-element-id"]}>
    <Form.Item label={props.label} required={props.required}>
      <Select
        mode="multiple"
        data-testid={`field-${props.name}`}
        options={(props.options ?? []).map((o) => ({ label: o, value: o }))}
      />
    </Form.Item>
  </FieldWrapper>
);

const LocationField: React.FC<{ props: BaseFieldProps }> = ({ props }) => (
  <FieldWrapper elementId={props["data-element-id"]}>
    <Form.Item label={props.label} required={props.required}>
      <Select
        data-testid={`field-${props.name}`}
        options={(
          props.options ?? ["United States", "Canada", "United Kingdom"]
        ).map((o) => ({ label: o, value: o }))}
      />
    </Form.Item>
  </FieldWrapper>
);

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
