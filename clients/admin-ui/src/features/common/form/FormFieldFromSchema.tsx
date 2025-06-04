import { Field, FieldInputProps } from "formik";

import {
  ConnectionTypeSecretSchemaProperty,
  ConnectionTypeSecretSchemaResponse,
} from "~/features/connection-type/types";

import { ControlledSelect } from "./ControlledSelect";
import { CustomNumberInput, CustomTextInput } from "./inputs";

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
  const enumDefinition = fieldSchema.allOf?.[0]?.$ref
    ? secretsSchema?.definitions[
        fieldSchema.allOf[0].$ref.replace("#/definitions/", "")
      ]
    : undefined;

  const isSelect = !!enumDefinition?.enum || fieldSchema.options;
  const isBoolean = fieldSchema.type === "boolean";
  const isInteger = fieldSchema.type === "integer";

  const getPlaceholder = () => {
    if (fieldSchema.allOf?.[0].$ref === "#/definitions/FidesDatasetReference") {
      return "Enter dataset.collection.field";
    }
    return undefined;
  };

  return (
    <Field id={name} name={name} key={name} validate={validate}>
      {({ field }: { field: FieldInputProps<string> }) => {
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
            <ControlledSelect
              name={field.name}
              key={field.name}
              id={field.name}
              label={fieldSchema.title}
              isRequired={isRequired}
              tooltip={fieldSchema.description}
              layout={layout}
              options={options}
              mode={fieldSchema.multiselect ? "multiple" : undefined}
            />
          );
        }

        if (isBoolean) {
          return (
            <ControlledSelect
              name={field.name}
              key={field.name}
              id={field.name}
              label={fieldSchema.title}
              isRequired={isRequired}
              tooltip={fieldSchema.description}
              layout={layout}
              options={[
                { label: "False", value: "false" },
                { label: "True", value: "true" },
              ]}
            />
          );
        }

        if (isInteger) {
          return (
            <CustomNumberInput
              {...field}
              label={fieldSchema.title}
              tooltip={fieldSchema.description}
              isRequired={isRequired}
              placeholder={getPlaceholder()}
              variant={layout}
            />
          );
        }

        return (
          <CustomTextInput
            {...field}
            label={fieldSchema.title}
            tooltip={fieldSchema.description}
            isRequired={isRequired}
            type={fieldSchema.sensitive ? "password" : "text"}
            placeholder={getPlaceholder()}
            autoComplete="off"
            color="gray.700"
            variant={layout}
          />
        );
      }}
    </Field>
  );
};
