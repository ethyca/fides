/**
 * Various common form inputs, styled specifically for Formik forms used throughout our app
 */

import {
  Box,
  EyeIcon,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  FormLabelProps,
  Grid,
  IconButton,
  Input,
  InputGroup,
  InputProps,
  InputRightElement,
  Radio,
  RadioGroup,
  Stack,
  Switch,
  Textarea,
  TextareaProps,
  VStack,
} from "@fidesui/react";
import { CreatableSelect, Select, Size } from "chakra-react-select";
import { FieldHookConfig, useField, useFormikContext } from "formik";
import { useState } from "react";

import QuestionTooltip from "~/features/common/QuestionTooltip";

interface CustomInputProps {
  disabled?: boolean;
  label: string;
  tooltip?: string;
  variant?: "inline" | "stacked";
}

// We allow `undefined` here and leave it up to each component that uses this field
// to handle the undefined case. Forms throw an error when their state goes to/from
// `undefined` (uncontrolled vs controlled). However, it is a lot more convenient if
// we can pass in `undefined` as a value from our object as opposed to having to transform
// it just for the form. Therefore, we have our form components do the work of transforming
// if the value they receive is undefined.
type StringField = FieldHookConfig<string | undefined>;
type StringArrayField = FieldHookConfig<string[] | undefined>;

const Label = ({
  title,
  ...labelProps
}: {
  title: string;
} & FormLabelProps) => (
  <FormLabel size="sm" {...labelProps}>
    {title}
  </FormLabel>
);

const TextInput = ({
  isPassword,
  ...props
}: InputProps & { isPassword: boolean }) => {
  const [type, setType] = useState<"text" | "password">(
    isPassword ? "password" : "text"
  );

  const handleClickReveal = () =>
    setType(type === "password" ? "text" : "password");

  return (
    <InputGroup size="sm" mr="2">
      <Input {...props} type={type} pr={isPassword ? "10" : "3"} />
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
  );
};

const ErrorMessage = ({
  isInvalid,
  message,
  fieldName,
}: {
  isInvalid: boolean;
  fieldName: string;
  message?: string;
}) => {
  if (!isInvalid) {
    return null;
  }
  return (
    <FormErrorMessage data-testid={`error-${fieldName}`}>
      {message}
    </FormErrorMessage>
  );
};

export const CustomTextInput = ({
  label,
  tooltip,
  disabled,
  variant = "inline",
  ...props
}: CustomInputProps & StringField) => {
  const [initialField, meta] = useField(props);
  const { type: initialType, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };

  const isPassword = initialType === "password";

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid}>
        <Grid templateColumns="1fr 3fr">
          <Label title={label} htmlFor={props.id || props.name} />
          <Box display="flex" alignItems="center">
            <TextInput
              {...field}
              isDisabled={disabled}
              data-testid={`input-${field.name}`}
              placeholder={placeholder}
              isPassword={isPassword}
            />
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Box>
        </Grid>
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
        />
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label
            title={label}
            htmlFor={props.id || props.name}
            fontSize="sm"
            my={0}
            mr={1}
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <TextInput
          {...field}
          isDisabled={disabled}
          data-testid={`input-${field.name}`}
          placeholder={placeholder}
          isPassword={isPassword}
        />
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
        />
      </VStack>
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
}: SelectProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);

  const selected = options.find((o) => o.value === field.value) || null;
  const { touched, setTouched } = useFormikContext();

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <Label title={label} htmlFor={props.id || props.name} />
        <Box
          display="flex"
          alignItems="center"
          data-testid={`input-${field.name}`}
        >
          <Select
            options={options}
            onBlur={(e) => {
              setTouched({ ...touched, [field.name]: true });
              field.onBlur(e);
            }}
            onChange={(newValue) => {
              if (newValue) {
                field.onChange(props.name)(newValue.value);
              } else if (isClearable) {
                field.onChange(props.name)("");
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
            instanceId={`select-${field.name}`}
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
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
}: SelectProps & StringArrayField) => {
  const [initialField, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? [] };
  const selected = options.filter((o) => field.value.indexOf(o.value) >= 0);

  // note: for Multiselect we have to do setFieldValue instead of field.onChange
  // because field.onChange only accepts strings or events right now, not string[]
  // https://github.com/jaredpalmer/formik/issues/1667
  const { setFieldValue, touched, setTouched } = useFormikContext();

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <Label title={label} htmlFor={props.id || props.name} />
        <Box
          display="flex"
          alignItems="center"
          data-testid={`input-${field.name}`}
        >
          <Select
            options={options}
            onBlur={(e) => {
              setTouched({ ...touched, [field.name]: true });
              field.onBlur(e);
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
            instanceId={`select-${field.name}`}
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
    </FormControl>
  );
};

export const CustomCreatableSingleSelect = ({
  label,
  isSearchable,
  options,
  ...props
}: SelectProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);
  const selected = { label: field.value, value: field.value };

  const { touched, setTouched } = useFormikContext();

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <Label title={label} htmlFor={props.id || props.name} />
        <Box data-testid={`input-${field.name}`}>
          <CreatableSelect
            options={options}
            onBlur={(e) => {
              setTouched({ ...touched, [field.name]: true });
              field.onBlur(e);
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
        </Box>
      </Grid>
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
    </FormControl>
  );
};

export const CustomCreatableMultiSelect = ({
  label,
  isSearchable,
  isClearable,
  options,
  size = "sm",
  tooltip,
  ...props
}: SelectProps & StringArrayField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? [] };
  const isInvalid = !!(meta.touched && meta.error);
  const selected = field.value.map((v) => ({ label: v, value: v }));
  const { setFieldValue, touched, setTouched } = useFormikContext();

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <Label title={label} htmlFor={props.id || props.name} />
        <Box
          display="flex"
          alignItems="center"
          data-testid={`input-${field.name}`}
        >
          <CreatableSelect
            data-testid={`input-${field.name}`}
            name={props.name}
            chakraStyles={{
              container: (provided) => ({ ...provided, mr: 2, flexGrow: 1 }),
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
            onBlur={(e) => {
              setTouched({ ...touched, [field.name]: true });
              field.onBlur(e);
            }}
            onChange={(newValue) => {
              setFieldValue(
                field.name,
                newValue.map((v) => v.value)
              );
            }}
            size={size}
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
    </FormControl>
  );
};

interface CustomTextAreaProps {
  textAreaProps?: TextareaProps;
  label?: string;
}
export const CustomTextArea = ({
  textAreaProps,
  label,
  ...props
}: CustomTextAreaProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);
  const InnerTextArea = (
    <Textarea
      {...field}
      size="sm"
      mr={2}
      {...textAreaProps}
      data-testid={`input-${field.name}`}
    />
  );

  return (
    <FormControl isInvalid={isInvalid}>
      {label ? (
        <Grid templateColumns="1fr 3fr">
          {label ? <FormLabel>{label}</FormLabel> : null}
          {InnerTextArea}
        </Grid>
      ) : (
        InnerTextArea
      )}
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
    </FormControl>
  );
};

interface CustomRadioGroupProps {
  label: string;
  options: Option[];
}
export const CustomRadioGroup = ({
  label,
  options,
  ...props
}: CustomRadioGroupProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);
  const selected = options.find((o) => o.value === field.value) ?? options[0];

  const handleChange = (o: string) => {
    field.onChange(props.name)(o);
  };

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <Label title={label} htmlFor={props.id || props.name} />
        <RadioGroup
          onChange={handleChange}
          value={selected.value}
          data-testid={`input-${field.name}`}
          colorScheme="secondary"
        >
          <Stack direction="row">
            {options.map((o) => (
              <Radio
                key={o.value}
                value={o.value}
                data-testid={`option-${o.value}`}
              >
                {o.label}
              </Radio>
            ))}
          </Stack>
        </RadioGroup>
      </Grid>
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
    </FormControl>
  );
};

interface CustomSwitchProps {
  label: string;
  tooltip?: string;
}
export const CustomSwitch = ({
  label,
  tooltip,
  ...props
}: CustomSwitchProps & FieldHookConfig<boolean>) => {
  const [field, meta] = useField({ ...props, type: "checkbox" });
  const isInvalid = !!(meta.touched && meta.error);

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr" justifyContent="center">
        <Label title={label} htmlFor={props.id || props.name} my={0} />
        <Box display="flex" alignItems="center">
          <Switch
            name={field.name}
            isChecked={field.checked}
            onChange={field.onChange}
            onBlur={field.onBlur}
            colorScheme="secondary"
            mr={2}
            data-testid={`input-${field.name}`}
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
    </FormControl>
  );
};
