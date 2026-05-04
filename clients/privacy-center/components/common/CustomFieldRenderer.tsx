import { Input, LocationSelect, Radio, Select } from "fidesui";
import { ReactNode } from "react";

import {
  CustomLocationField,
  CustomMultiSelectField,
  CustomRadioField,
  CustomSelectField,
  CustomTextField,
  ICustomField,
} from "~/types/config";

interface ICustomFieldProps extends ICustomField {
  onBlur: () => void;
  fieldKey: string;
  error?: ReactNode;
}

interface ICustomTextFieldProps extends CustomTextField, ICustomFieldProps {
  value: string;
  onChange: (value: string) => void;
}

interface ICustomSelectFieldProps extends CustomSelectField, ICustomFieldProps {
  value: string;
  onChange: (value: string) => void;
}

interface ICustomRadioFieldProps extends CustomRadioField, ICustomFieldProps {
  value: string;
  onChange: (value: string) => void;
}

interface ICustomMultiSelectFieldProps
  extends CustomMultiSelectField, ICustomFieldProps {
  value: Array<string>;
  onChange: (value: Array<string>) => void;
}

interface ICustomLocationFieldProps
  extends CustomLocationField, ICustomFieldProps {
  value: string;
  onChange: (value: string) => void;
}

export type CustomFieldRendererProps =
  | ICustomTextFieldProps
  | ICustomSelectFieldProps
  | ICustomRadioFieldProps
  | ICustomMultiSelectFieldProps
  | ICustomLocationFieldProps;

const CustomFieldRenderer = ({
  fieldKey,
  label,
  onBlur,
  required,
  ...props
}: CustomFieldRendererProps) => {
  switch (props.field_type) {
    case "select":
      return (
        <Select
          id={fieldKey}
          data-testid={`select-${fieldKey}`}
          placeholder={props.placeholder ?? `Select ${label.toLowerCase()}`}
          value={props.value}
          onChange={(selectedValue) => {
            props.onChange(selectedValue);
          }}
          onBlur={onBlur}
          options={props.options?.map((option: string) => ({
            label: option,
            value: option,
          }))}
          getPopupContainer={() => document.body}
          styles={{
            popup: {
              root: {
                maxHeight: 400,
                overflow: "auto",
                zIndex: 1500,
              },
            },
          }}
          classNames={{
            popup: {
              root: "privacy-form-dropdown",
            },
          }}
          allowClear
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={required !== false}
        />
      );

    case "radio":
      return (
        <Radio.Group
          id={fieldKey}
          data-testid={`radio-${fieldKey}`}
          value={props.value !== "" ? props.value : undefined}
          onChange={(e) => props.onChange(e.target.value)}
          onBlur={onBlur}
          options={props.options?.map((option: string) => ({
            label: option,
            value: option,
          }))}
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={required !== false}
        />
      );

    case "multiselect":
      return (
        <Select
          id={fieldKey}
          data-testid={`select-${fieldKey}`}
          mode="multiple"
          placeholder={props.placeholder ?? `Select ${label.toLowerCase()}`}
          value={props.value}
          onChange={props.onChange}
          onBlur={onBlur}
          options={props.options?.map((option) => ({
            label: option,
            value: option,
          }))}
          getPopupContainer={() => document.body}
          styles={{
            popup: {
              root: {
                maxHeight: 400,
                overflow: "auto",
                zIndex: 1500,
              },
            },
          }}
          classNames={{
            popup: {
              root: "privacy-form-dropdown",
            },
          }}
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={required !== false}
        />
      );

    case "location":
      return (
        <LocationSelect
          id={fieldKey}
          data-testid={`location-select-${fieldKey}`}
          placeholder={props.placeholder ?? `Select ${label.toLowerCase()}`}
          value={props.value !== "" ? props.value : undefined}
          onChange={props.onChange}
          onBlur={onBlur}
          getPopupContainer={() => document.body}
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={required !== false}
        />
      );

    case "text":
    default:
      return (
        <Input
          id={fieldKey}
          name={fieldKey}
          placeholder={props.placeholder ?? label}
          onChange={(e) => props.onChange(e.target.value)}
          onBlur={onBlur}
          value={props.value}
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={required !== false}
        />
      );
  }
};

export default CustomFieldRenderer;
