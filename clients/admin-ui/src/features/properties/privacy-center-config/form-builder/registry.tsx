import { defineRegistry, useStateBinding } from "@json-render/react";
import { Form, Input, Radio, Select } from "fidesui";
import dynamic from "next/dynamic";
import React, { useEffect, useRef } from "react";

import { catalog } from "./catalog";

// LocationField pulls in fidesui's LocationSelect, which transitively imports
// iso-3166 (CJS). Turbopack rejects that on the SSR path with "CJS module
// can't be async." Loading the field via next/dynamic with ssr:false keeps
// it client-only and avoids polluting the synchronous chunk.
const LocationField = dynamic(
  () => import("./LocationField").then((m) => m.LocationField),
  { ssr: false },
);

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

/**
 * Seed the field's binding from `default_value`:
 * - On first mount when nothing is in state yet.
 * - When the author changes `default_value` in the properties panel and the
 *   field is either empty or still showing the previous default. This keeps
 *   the Edit-mode preview in sync with the property the author just edited.
 *
 * If the end user has typed something different, we leave their value alone.
 */
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
    // setValue is stable (state-binding setter). Re-running on every value
    // change would clobber user input — we intentionally trigger only on
    // defaultValue changes plus the initial mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stableValueKey(defaultValue)]);
};

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
  },
});
