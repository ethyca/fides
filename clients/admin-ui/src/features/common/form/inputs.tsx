import {
  Box,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Grid,
  IconButton,
  Input,
  InputGroup,
  InputRightElement,
  Textarea,
  TextareaProps,
} from "@fidesui/react";
import { CreatableSelect, Select, Size } from "chakra-react-select";
import { FieldHookConfig, useField, useFormikContext } from "formik";
import { useState } from "react";

import { EyeIcon } from "~/features/common/Icon";
import QuestionTooltip from "~/features/common/QuestionTooltip";

interface InputProps {
  disabled?: boolean;
  label: string;
  tooltip?: string;
  "data-testid"?: string;
}

export const CustomTextInput = ({
  label,
  tooltip,
  ...props
}: InputProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const { type: initialType, placeholder, "data-testid": dataTestId } = props;
  const isInvalid = !!(meta.touched && meta.error);

  const isPassword = initialType === "password";
  const [type, setType] = useState<"text" | "password">(
    isPassword ? "password" : "text"
  );

  const handleClickReveal = () =>
    setType(type === "password" ? "text" : "password");

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <Box display="flex" alignItems="center">
          <InputGroup size="sm" mr="2">
            <Input
              {...field}
              data-testid={dataTestId}
              type={type}
              placeholder={placeholder}
              pr={isPassword ? "10" : "3"}
            />
            {isPassword ? (
              <InputRightElement pr="2">
                <IconButton
                  size="xs"
                  variant="unstyled"
                  aria-label="Reveal/Hide Secret"
                  icon={
                    <EyeIcon
                      boxSize="full"
                      color={type === "password" ? "gray.400" : "gray.700"}
                    />
                  }
                  onClick={handleClickReveal}
                />
              </InputRightElement>
            ) : null}
          </InputGroup>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

export interface Option {
  value: string;
  label: string;
}
interface SelectProps {
  label: string;
  tooltip?: string;
  options: Option[];
  isSearchable?: boolean;
  isClearable?: boolean;
  size?: Size;
  "data-testid"?: string;
}
export const CustomSelect = ({
  label,
  tooltip,
  options,
  isSearchable,
  isClearable,
  size = "sm",
  ...props
}: SelectProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);

  const selected = options.find((o) => o.value === field.value) || null;

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <Box
          display="flex"
          alignItems="center"
          data-testid={props["data-testid"]}
        >
          <Select
            options={options}
            onBlur={(option) => {
              if (option) {
                field.onBlur(props.name);
              }
            }}
            onChange={(newValue) => {
              if (newValue) {
                field.onChange(props.name)(newValue.value);
              }
            }}
            name={props.name}
            value={selected}
            size={size}
            chakraStyles={{
              container: (provided) => ({ ...provided, mr: 2, flexGrow: 1 }),
              dropdownIndicator: (provided) => ({
                ...provided,
                bg: "transparent",
                px: 2,
                cursor: "inherit",
              }),
              indicatorSeparator: (provided) => ({
                ...provided,
                display: "none",
              }),
              multiValue: (provided) => ({
                ...provided,
                background: "primary.400",
                color: "white",
              }),
            }}
            isSearchable={isSearchable ?? false}
            isClearable={isClearable}
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

// mostly the same as CustomSelect except can handle multiple values
// the types are easier when this is a separate component as opposed to
// extending CustomSelect
export const CustomMultiSelect = ({
  label,
  tooltip,
  options,
  isSearchable,
  isClearable,
  size = "sm",
  ...props
}: SelectProps & FieldHookConfig<string[]>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  const selected = options.filter((o) => field.value.indexOf(o.value) >= 0);

  // note: for Multiselect we have to do setFieldValue instead of field.onChange
  // because field.onChange only accepts strings or events right now, not string[]
  // https://github.com/jaredpalmer/formik/issues/1667
  const { setFieldValue } = useFormikContext();

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <Box
          display="flex"
          alignItems="center"
          data-testid={props["data-testid"]}
        >
          <Select
            options={options}
            onBlur={(option) => {
              if (option) {
                field.onBlur(props.name);
              }
            }}
            onChange={(newValue) => {
              setFieldValue(
                field.name,
                newValue.map((v) => v.value)
              );
            }}
            name={props.name}
            value={selected}
            size={size}
            chakraStyles={{
              container: (provided) => ({ ...provided, mr: 2, flexGrow: 1 }),
              dropdownIndicator: (provided) => ({
                ...provided,
                bg: "transparent",
                px: 2,
                cursor: "inherit",
              }),
              indicatorSeparator: (provided) => ({
                ...provided,
                display: "none",
              }),
              multiValue: (provided) => ({
                ...provided,
                background: "primary.400",
                color: "white",
              }),
            }}
            components={{
              ClearIndicator: () => null,
            }}
            isSearchable={isSearchable}
            isClearable={isClearable}
            isMulti
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

export const CustomCreatableSingleSelect = ({
  label,
  isSearchable,
  options,
  ...props
}: SelectProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  const selected = { label: field.value, value: field.value };

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <FormLabel htmlFor={props.id || props.name}>{label}</FormLabel>
        <CreatableSelect
          options={options}
          onBlur={(option) => {
            if (option) {
              field.onBlur(props.name);
            }
          }}
          onChange={(newValue) => {
            if (newValue) {
              field.onChange(props.name)(newValue.value);
            } else {
              field.onChange(props.name)("");
            }
          }}
          name={props.name}
          value={selected}
          chakraStyles={{
            dropdownIndicator: (provided) => ({
              ...provided,
              background: "white",
            }),
            multiValue: (provided) => ({
              ...provided,
              background: "primary.400",
              color: "white",
            }),
            multiValueRemove: (provided) => ({
              ...provided,
              display: "none",
              visibility: "hidden",
            }),
          }}
        />
      </Grid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

export const CustomCreatableMultiSelect = ({
  label,
  isSearchable,
  isClearable,
  options,
  ...props
}: SelectProps & FieldHookConfig<string[]>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  const selected = field.value.map((v) => ({ label: v, value: v }));
  const { setFieldValue } = useFormikContext();

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <FormLabel htmlFor={props.id || props.name}>{label}</FormLabel>
        <CreatableSelect
          name={props.name}
          chakraStyles={{
            dropdownIndicator: (provided) => ({
              ...provided,
              background: "white",
            }),
            multiValue: (provided) => ({
              ...provided,
              background: "primary.400",
              color: "white",
            }),
            multiValueRemove: (provided) => ({
              ...provided,
              display: "none",
              visibility: "hidden",
            }),
          }}
          components={{
            Menu: () => null,
            DropdownIndicator: () => null,
          }}
          isClearable={isClearable}
          isMulti
          options={options}
          value={selected}
          onBlur={(option) => {
            if (option) {
              field.onBlur(props.name);
            }
          }}
          onChange={(newValue) => {
            setFieldValue(
              field.name,
              newValue.map((v) => v.value)
            );
          }}
        />
      </Grid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

export const CustomTextArea = ({
  textAreaProps,
  ...props
}: { textAreaProps?: TextareaProps } & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  return (
    <FormControl isInvalid={isInvalid}>
      <Textarea {...field} size="sm" mb={2} {...textAreaProps} />
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
