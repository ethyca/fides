import {
  Button,
  Checkbox,
  Input,
  LocationSelect,
  Select,
  Upload,
  UploadFile,
} from "fidesui";
import { ReactNode } from "react";

import {
  CustomCheckboxField,
  CustomCheckboxGroupField,
  CustomFileUploadField,
  CustomLocationField,
  CustomMultiSelectField,
  CustomSelectField,
  CustomTextareaField,
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

interface ICustomMultiSelectFieldProps
  extends CustomMultiSelectField, ICustomFieldProps {
  value: Array<string>;
  onChange: (value: Array<string>) => void;
}

interface ICustomCheckboxFieldProps
  extends CustomCheckboxField, ICustomFieldProps {
  value: boolean;
  onChange: (value: boolean) => void;
}

interface ICustomCheckboxGroupFieldProps
  extends CustomCheckboxGroupField, ICustomFieldProps {
  value: Array<string>;
  onChange: (value: Array<string>) => void;
}

interface ICustomTextareaFieldProps
  extends CustomTextareaField, ICustomFieldProps {
  value: string;
  onChange: (value: string) => void;
}

interface ICustomFileUploadFieldProps
  extends CustomFileUploadField, ICustomFieldProps {
  value: UploadFile[];
  onChange: (fileList: UploadFile[]) => void;
}

interface ICustomLocationFieldProps
  extends CustomLocationField, ICustomFieldProps {
  value: string;
  onChange: (value: string) => void;
}

export type CustomFieldRendererProps =
  | ICustomTextFieldProps
  | ICustomSelectFieldProps
  | ICustomMultiSelectFieldProps
  | ICustomCheckboxFieldProps
  | ICustomCheckboxGroupFieldProps
  | ICustomTextareaFieldProps
  | ICustomFileUploadFieldProps
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
          placeholder={`Select ${label.toLowerCase()}`}
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

    case "multiselect":
      return (
        <Select
          id={fieldKey}
          data-testid={`select-${fieldKey}`}
          mode="multiple"
          placeholder={`Select ${label.toLowerCase()}`}
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

    case "checkbox":
      return (
        <Checkbox
          id={fieldKey}
          data-testid={`checkbox-${fieldKey}`}
          checked={props.value}
          onChange={(e) => {
            props.onChange(e.target.checked);
            onBlur();
          }}
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={required !== false}
        >
          {label}
        </Checkbox>
      );

    case "checkbox_group":
      return (
        <Checkbox.Group
          data-testid={`checkbox-group-${fieldKey}`}
          value={props.value}
          onChange={(checkedValues) => {
            props.onChange(checkedValues as string[]);
            onBlur();
          }}
          options={props.options?.map((option) => ({
            label: option,
            value: option,
          }))}
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
        />
      );

    case "textarea":
      return (
        <Input.TextArea
          id={fieldKey}
          name={fieldKey}
          placeholder={label}
          onChange={(e) => props.onChange(e.target.value)}
          onBlur={onBlur}
          value={props.value}
          rows={4}
          aria-label={label}
          aria-describedby={`${fieldKey}-error`}
          aria-required={required !== false}
        />
      );

    case "file":
      return (
        <Upload
          fileList={props.value}
          onChange={({ fileList: newFileList }) => {
            props.onChange(newFileList);
            onBlur();
          }}
          beforeUpload={() => false}
          multiple
          accept={props.allowed_mime_types?.join(",")}
          data-testid={`file-upload-${fieldKey}`}
        >
          <Button data-testid={`file-upload-button-${fieldKey}`}>
            Click to upload
          </Button>
        </Upload>
      );

    case "location":
      return (
        <LocationSelect
          id={fieldKey}
          data-testid={`location-select-${fieldKey}`}
          placeholder={`Select ${label.toLowerCase()}`}
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
          placeholder={label}
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
