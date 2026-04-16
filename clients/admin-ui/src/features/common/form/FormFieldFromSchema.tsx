import { Form, Input, Select } from "fidesui";

import { FIDES_DATASET_REFERENCE } from "~/features/common/form/useFormFieldsFromSchema";
import {
  ConnectionTypeSecretSchemaProperty,
  ConnectionTypeSecretSchemaResponse,
} from "~/features/connection-type/types";

export type FormFieldProps = {
  name: string;
  fieldSchema: ConnectionTypeSecretSchemaProperty;
  isRequired: boolean;
  layout?: "stacked" | "inline";
  secretsSchema?: ConnectionTypeSecretSchemaResponse;
  validate?: (value: string | undefined) => string | undefined;
};

export const FormFieldFromSchema = ({
  name,
  fieldSchema,
  isRequired,
  layout = "stacked",
  secretsSchema,
  validate,
}: FormFieldProps) => {
  const enumDefinition =
    fieldSchema.allOf?.[0]?.$ref &&
    fieldSchema.allOf[0].$ref !== FIDES_DATASET_REFERENCE
      ? secretsSchema?.definitions[
          fieldSchema.allOf[0].$ref.replace("#/definitions/", "")
        ]
      : undefined;

  const isSelect = !!enumDefinition?.enum || fieldSchema.options;
  const isBoolean = fieldSchema.type === "boolean";

  const getPlaceholder = () => {
    if (fieldSchema.allOf?.[0].$ref === FIDES_DATASET_REFERENCE) {
      return "Enter dataset.collection.field";
    }
    return undefined;
  };

  const rules = [
    ...(isRequired
      ? [{ required: true, message: `${fieldSchema.title} is required` }]
      : []),
    ...(validate
      ? [
          {
            validator: (_: unknown, value: string | undefined) => {
              const error = validate(value);
              return error
                ? Promise.reject(new Error(error))
                : Promise.resolve();
            },
          },
        ]
      : []),
  ];

  const formItemProps = {
    name: name.split("."),
    label: fieldSchema.title,
    tooltip: fieldSchema.description,
    rules,
    layout: layout === "inline" ? ("horizontal" as const) : undefined,
  };

  if (isSelect) {
    const options =
      enumDefinition?.enum?.map((value) => ({
        label: value,
        value,
      })) ??
      fieldSchema.options?.map((option) => ({
        label: option,
        value: option,
      }));

    return (
      <Form.Item {...formItemProps}>
        <Select
          aria-label={fieldSchema.title}
          data-testid={`controlled-select-${name}`}
          options={options}
          mode={fieldSchema.multiselect ? "multiple" : undefined}
        />
      </Form.Item>
    );
  }

  if (isBoolean) {
    return (
      <Form.Item {...formItemProps}>
        <Select
          aria-label={fieldSchema.title}
          data-testid={`controlled-select-${name}`}
          options={[
            { label: "False", value: "false" },
            { label: "True", value: "true" },
          ]}
        />
      </Form.Item>
    );
  }

  // Use textarea for multiline fields, but prioritize password input for sensitive fields
  if (fieldSchema.multiline && !fieldSchema.sensitive) {
    return (
      <Form.Item {...formItemProps}>
        <Input.TextArea
          data-testid={`input-${name}`}
          rows={8}
          style={{ fontFamily: "monospace", fontSize: "12px" }}
          placeholder={getPlaceholder()}
        />
      </Form.Item>
    );
  }

  if (fieldSchema.sensitive) {
    return (
      <Form.Item {...formItemProps}>
        <Input.Password
          data-testid={`input-${name}`}
          placeholder={getPlaceholder()}
          autoComplete="off"
        />
      </Form.Item>
    );
  }

  return (
    <Form.Item {...formItemProps}>
      <Input
        data-testid={`input-${name}`}
        placeholder={getPlaceholder()}
        autoComplete="off"
      />
    </Form.Item>
  );
};
