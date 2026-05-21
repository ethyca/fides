import { defineRegistry, useStateBinding } from "@json-render/react";
import { Form, Input, Radio, Select } from "fidesui";
import dynamic from "next/dynamic";
import React from "react";

import { catalog } from "./catalog";
import {
  BaseFieldProps,
  FieldWrapper,
  IdentityFieldProps,
  useDefaultValueSeed,
} from "./fieldUtils";

// LocationField pulls in fidesui's LocationSelect, which transitively imports
// iso-3166 (CJS). Turbopack rejects that on the SSR path with "CJS module
// can't be async." Loading the field via next/dynamic with ssr:false keeps
// it client-only and avoids polluting the synchronous chunk.
const LocationField = dynamic(
  () => import("./LocationField").then((m) => m.LocationField),
  { ssr: false },
);

// PhoneField uses react-phone-number-input which bundles flag SVGs and
// ships its own CSS — client-only for the same reason as LocationField.
const PhoneFieldDynamic = dynamic(
  () => import("./PhoneField").then((m) => m.PhoneField),
  { ssr: false },
);

const FormContainer = ({ children }: { children?: React.ReactNode }) => (
  <Form layout="vertical">{children}</Form>
);

// Each field binds its current value to /form/<name> in the json-render
// state model. In Preview mode this lets visibility conditions react to
// user input (e.g. show field B when /form/country eq "US"). In Edit mode
// each field has its own isolated provider, so the binding is harmless.
const useFieldBinding = <T,>(name: string) =>
  useStateBinding<T>(`/form/${name}`);

const TextField = ({ props }: { props: BaseFieldProps }) => {
  const [value, setValue] = useFieldBinding<string>(props.name);
  useDefaultValueSeed(
    value,
    setValue,
    props.default_value as string | undefined,
  );
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
  useDefaultValueSeed(
    value,
    setValue,
    props.default_value as string | undefined,
  );
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
  useDefaultValueSeed(
    value,
    setValue,
    props.default_value as string[] | undefined,
  );
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

const EmailField = ({ props }: { props: IdentityFieldProps }) => {
  const [value, setValue] = useFieldBinding<string>("email");
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label="Email" required={props.required}>
        <Input
          aria-label="Email"
          data-testid="field-email"
          placeholder="your-email@example.com"
          type="email"
          value={value ?? ""}
          onChange={(e) => setValue(e.target.value)}
        />
      </Form.Item>
    </FieldWrapper>
  );
};

const NameField = ({ props }: { props: IdentityFieldProps }) => {
  const [value, setValue] = useFieldBinding<string>("name");
  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label="Name" required={props.required}>
        <Input
          aria-label="Name"
          data-testid="field-name"
          placeholder="Jane Smith"
          value={value ?? ""}
          onChange={(e) => setValue(e.target.value)}
        />
      </Form.Item>
    </FieldWrapper>
  );
};

const RadioField = ({ props }: { props: BaseFieldProps }) => {
  const [value, setValue] = useFieldBinding<string>(props.name);
  useDefaultValueSeed(
    value,
    setValue,
    props.default_value as string | undefined,
  );
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
    Email: ({ props }) => <EmailField props={props as IdentityFieldProps} />,
    Name: ({ props }) => <NameField props={props as IdentityFieldProps} />,
    Phone: ({ props }) => (
      <PhoneFieldDynamic props={props as IdentityFieldProps} />
    ),
  },
});
