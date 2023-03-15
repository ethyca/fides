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
import {
  CreatableSelect,
  MenuPosition,
  MultiValue,
  Select,
  SingleValue,
  Size,
} from "chakra-react-select";
import { FieldHookConfig, useField, useFormikContext } from "formik";
import { useState } from "react";

import QuestionTooltip from "~/features/common/QuestionTooltip";

type Variant = "inline" | "stacked" | "block";

interface CustomInputProps {
  disabled?: boolean;
  label: string;
  tooltip?: string;
  variant?: Variant;
  isRequired?: boolean;
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
  children,
  ...labelProps
}: {
  children: React.ReactNode;
} & FormLabelProps) => (
  <FormLabel size="sm" {...labelProps}>
    {children}
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
      <Input
        {...props}
        type={type}
        pr={isPassword ? "10" : "3"}
        background="white"
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

export interface Option {
  value: string;
  label: string;
}
interface SelectProps {
  label: string;
  labelProps?: FormLabelProps;
  tooltip?: string;
  options: Option[];
  isDisabled?: boolean;
  isSearchable?: boolean;
  isClearable?: boolean;
  isRequired?: boolean;
  size?: Size;
  isMulti?: boolean;
  variant?: Variant;
  menuPosition?: MenuPosition;
  /**
   * If true, when isMulti=false, the selected value will be rendered as a block,
   * similar to how the multi values are rendered
   */
  singleValueBlock?: boolean;
}
const SelectInput = ({
  options,
  fieldName,
  size,
  isSearchable,
  isClearable,
  isMulti = false,
  singleValueBlock,
  isDisabled = false,
  menuPosition = "absolute",
}: { fieldName: string; isMulti?: boolean } & Omit<SelectProps, "label">) => {
  const [initialField] = useField(fieldName);
  const field = { ...initialField, value: initialField.value ?? "" };
  const selected = isMulti
    ? options.filter((o) => field.value.indexOf(o.value) >= 0)
    : options.find((o) => o.value === field.value) || null;

  // note: for Multiselect we have to do setFieldValue instead of field.onChange
  // because field.onChange only accepts strings or events right now, not string[]
  // https://github.com/jaredpalmer/formik/issues/1667
  const { setFieldValue, touched, setTouched } = useFormikContext();

  const handleChangeMulti = (newValue: MultiValue<Option>) => {
    setFieldValue(
      field.name,
      newValue.map((v) => v.value)
    );
  };
  const handleChangeSingle = (newValue: SingleValue<Option>) => {
    if (newValue) {
      field.onChange(fieldName)(newValue.value);
    } else if (isClearable) {
      field.onChange(fieldName)("");
    }
  };

  const handleChange = (newValue: MultiValue<Option> | SingleValue<Option>) =>
    isMulti
      ? handleChangeMulti(newValue as MultiValue<Option>)
      : handleChangeSingle(newValue as SingleValue<Option>);

  const components = isClearable ? undefined : { ClearIndicator: () => null };

  return (
    <Select
      options={options}
      onBlur={(e) => {
        setTouched({ ...touched, [field.name]: true });
        field.onBlur(e);
      }}
      onChange={handleChange}
      name={fieldName}
      value={selected}
      size={size}
      classNamePrefix="custom-select"
      chakraStyles={{
        container: (provided) => ({
          ...provided,
          mr: 2,
          flexGrow: 1,
          backgroundColor: "white",
        }),
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
        singleValue: singleValueBlock
          ? (provided) => ({
              ...provided,
              background: "primary.400",
              color: "white",
              borderRadius: ".375rem",
              fontSize: ".75rem",
              paddingX: ".5rem",
            })
          : undefined,
      }}
      components={components}
      isSearchable={isSearchable}
      isClearable={isClearable}
      instanceId={`select-${field.name}`}
      isMulti={isMulti}
      isDisabled={isDisabled}
      menuPosition={menuPosition}
    />
  );
};

interface CreatableSelectProps extends SelectProps {
  /** Do not render the dropdown menu */
  disableMenu?: boolean;
}
const CreatableSelectInput = ({
  options,
  fieldName,
  size,
  isSearchable,
  isClearable,
  isMulti,
  disableMenu,
}: { fieldName: string } & Omit<CreatableSelectProps, "label">) => {
  const [initialField] = useField(fieldName);
  const value: string[] | string = initialField.value ?? [];
  const field = { ...initialField, value };
  const selected = Array.isArray(field.value)
    ? field.value.map((v) => ({ label: v, value: v }))
    : { label: field.value, value: field.value };

  const { setFieldValue, touched, setTouched } = useFormikContext();

  const handleChangeMulti = (newValue: MultiValue<Option>) => {
    setFieldValue(
      field.name,
      newValue.map((v) => v.value)
    );
  };
  const handleChangeSingle = (newValue: SingleValue<Option>) => {
    if (newValue) {
      field.onChange(field.name)(newValue.value);
    } else {
      field.onChange(field.name)("");
    }
  };

  const handleChange = (newValue: MultiValue<Option> | SingleValue<Option>) =>
    isMulti
      ? handleChangeMulti(newValue as MultiValue<Option>)
      : handleChangeSingle(newValue as SingleValue<Option>);

  const components = disableMenu
    ? { Menu: () => null, DropdownIndicator: () => null }
    : undefined;

  return (
    <CreatableSelect
      options={options}
      onBlur={(e) => {
        setTouched({ ...touched, [field.name]: true });
        field.onBlur(e);
      }}
      onChange={handleChange}
      name={fieldName}
      value={selected}
      size={size}
      classNamePrefix="custom-creatable-select"
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
      components={components}
      isSearchable={isSearchable}
      isClearable={isClearable}
      instanceId={`creatable-select-${fieldName}`}
      isMulti={isMulti}
    />
  );
};

export const CustomTextInput = ({
  label,
  tooltip,
  disabled,
  variant = "inline",
  isRequired = false,
  ...props
}: CustomInputProps & StringField) => {
  const [initialField, meta] = useField(props);
  const { type: initialType, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };

  const isPassword = initialType === "password";

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns="1fr 3fr">
          <Label htmlFor={props.id || props.name}>{label}</Label>
          <Flex alignItems="center">
            <Flex flexDir="column" flexGrow={1}>
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
            </Flex>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="sm" my={0} mr={1}>
            {label}
          </Label>
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

export const CustomSelect = ({
  label,
  labelProps,
  tooltip,
  options,
  isDisabled,
  isRequired,
  isSearchable,
  isClearable,
  size = "sm",
  isMulti,
  variant = "inline",
  singleValueBlock,
  ...props
}: SelectProps & StringField) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns="1fr 3fr">
          <Label htmlFor={props.id || props.name} {...labelProps}>
            {label}
          </Label>
          <Flex alignItems="center" data-testid={`input-${field.name}`}>
            <Flex flexDir="column" flexGrow={1}>
              <SelectInput
                options={options}
                fieldName={field.name}
                size={size}
                isSearchable={
                  isSearchable === undefined ? isMulti : isSearchable
                }
                isClearable={isClearable}
                isMulti={isMulti}
                isDisabled={isDisabled}
                singleValueBlock={singleValueBlock}
                menuPosition={props.menuPosition}
              />
              <ErrorMessage
                isInvalid={isInvalid}
                message={meta.error}
                fieldName={field.name}
              />
            </Flex>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label
            htmlFor={props.id || props.name}
            fontSize="sm"
            my={0}
            mr={1}
            {...labelProps}
          >
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <Box width="100%" data-testid={`input-${field.name}`}>
          <SelectInput
            options={options}
            fieldName={field.name}
            size={size}
            isSearchable={isSearchable === undefined ? isMulti : isSearchable}
            isClearable={isClearable}
            isMulti={isMulti}
            singleValueBlock={singleValueBlock}
            isDisabled={isDisabled}
            menuPosition={props.menuPosition}
          />
        </Box>
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
        />
      </VStack>
    </FormControl>
  );
};

export const CustomCreatableSelect = ({
  label,
  isSearchable = true,
  options,
  size = "sm",
  tooltip,
  variant = "inline",
  ...props
}: CreatableSelectProps & StringArrayField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? [] };
  const isInvalid = !!(meta.touched && meta.error);

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid}>
        <Grid templateColumns="1fr 3fr">
          <Label htmlFor={props.id || props.name}>{label}</Label>
          <Flex alignItems="center" data-testid={`input-${field.name}`}>
            <Flex flexDir="column" flexGrow={1}>
              <CreatableSelectInput
                fieldName={field.name}
                options={options}
                size={size}
                isSearchable={isSearchable}
                {...props}
              />
              <ErrorMessage
                isInvalid={isInvalid}
                message={meta.error}
                fieldName={field.name}
              />
            </Flex>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="sm" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <Box width="100%">
          <CreatableSelectInput
            fieldName={field.name}
            options={options}
            size={size}
            isSearchable={isSearchable}
            {...props}
          />
        </Box>
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
        />
      </VStack>
    </FormControl>
  );
};

interface CustomTextAreaProps {
  textAreaProps?: TextareaProps;
  label?: string;
  tooltip?: string;
  variant?: Variant;
}
export const CustomTextArea = ({
  textAreaProps,
  label,
  tooltip,
  variant = "inline",
  ...props
}: CustomTextAreaProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);
  const innerTextArea = (
    <Textarea
      {...field}
      size="sm"
      mr={2}
      {...textAreaProps}
      data-testid={`input-${field.name}`}
    />
  );

  // When there is no label, it doesn't matter if stacked or inline
  // since we only render the text field
  if (!label) {
    return (
      <FormControl isInvalid={isInvalid}>
        <Flex>
          <Flex flexDir="column" flexGrow={1}>
            {innerTextArea}
            <ErrorMessage
              isInvalid={isInvalid}
              message={meta.error}
              fieldName={field.name}
            />
          </Flex>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
      </FormControl>
    );
  }

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid}>
        <Grid templateColumns="1fr 3fr">
          {label ? <FormLabel>{label}</FormLabel> : null}
          <Flex>
            <Flex flexDir="column" flexGrow={1}>
              {innerTextArea}
              <ErrorMessage
                isInvalid={isInvalid}
                message={meta.error}
                fieldName={field.name}
              />
            </Flex>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="sm" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        {innerTextArea}
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
        />
      </VStack>
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
        <Label htmlFor={props.id || props.name}>{label}</Label>
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
        <Label htmlFor={props.id || props.name} my={0}>
          {label}
        </Label>
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
