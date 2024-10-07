/**
 * Various common form inputs, styled specifically for Formik forms used throughout our app
 */

import {
  chakraComponents,
  ChakraStylesConfig,
  CreatableSelect,
  GroupBase,
  MenuPosition,
  MultiValue,
  OptionProps,
  Select,
  SelectComponentsConfig,
  SingleValue,
  Size,
} from "chakra-react-select";
import {
  AntButton,
  AntSwitch as Switch,
  Box,
  Checkbox,
  Code,
  EyeIcon,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  FormLabelProps,
  forwardRef,
  Grid,
  HStack,
  Input,
  InputGroup,
  InputProps,
  InputRightElement,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Radio,
  RadioGroup,
  Stack,
  Text,
  Textarea,
  TextareaProps,
  VStack,
} from "fidesui";
import {
  Field,
  FieldHookConfig,
  FieldProps,
  useField,
  useFormikContext,
} from "formik";
import React, {
  LegacyRef,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import QuestionTooltip from "~/features/common/QuestionTooltip";

type Variant = "inline" | "stacked" | "block";

export interface CustomInputProps {
  disabled?: boolean;
  label?: string;
  tooltip?: string | null;
  variant?: Variant;
  isRequired?: boolean;
  textColor?: string;
  inputRightElement?: React.ReactNode;
  size?: string;
  placeholder?: string;
}

// We allow `undefined` here and leave it up to each component that uses this field
// to handle the undefined case. Forms throw an error when their state goes to/from
// `undefined` (uncontrolled vs controlled). However, it is a lot more convenient if
// we can pass in `undefined` as a value from our object as opposed to having to transform
// it just for the form. Therefore, we have our form components do the work of transforming
// if the value they receive is undefined.
export type StringField = FieldHookConfig<string | undefined>;
type StringArrayField = FieldHookConfig<string[] | undefined>;

export const Label = ({
  children,
  ...labelProps
}: {
  children: React.ReactNode;
} & FormLabelProps) => (
  <FormLabel size="sm" {...labelProps}>
    {children}
  </FormLabel>
);

export const TextInput = forwardRef(
  (
    {
      isPassword,
      inputRightElement,
      size,
      ...props
    }: InputProps & {
      isPassword: boolean;
      inputRightElement?: React.ReactNode;
    },
    ref,
  ) => {
    const [type, setType] = useState<"text" | "password">(
      isPassword ? "password" : "text",
    );

    const handleClickReveal = () =>
      setType(type === "password" ? "text" : "password");

    return (
      <InputGroup size={size ?? "sm"}>
        <Input
          {...props}
          ref={ref as LegacyRef<HTMLInputElement> | undefined}
          type={type}
          pr={isPassword ? "10" : "3"}
          background="white"
          focusBorderColor="primary.600"
        />
        {inputRightElement ? (
          <InputRightElement pr={2}>{inputRightElement}</InputRightElement>
        ) : null}
        {isPassword ? (
          <InputRightElement pr="2">
            <AntButton
              size="small"
              type="text"
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
  },
);
TextInput.displayName = "TextInput";

export const ErrorMessage = ({
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

const ClearIndicator = () => null;

export interface Option {
  value: string;
  label: string;
  description?: string | null;
  tooltip?: string;
}

const CustomOption = ({
  children,
  ...props
}: OptionProps<Option, boolean, GroupBase<Option>>) => (
  <chakraComponents.Option {...props}>
    <Flex flexDirection="column" padding={2}>
      <Text color="gray.700" fontSize="14px" lineHeight={5} fontWeight="medium">
        {props.data.label}
      </Text>

      {props.data.description ? (
        <Text
          color="gray.500"
          fontSize="12px"
          lineHeight={4}
          fontWeight="normal"
        >
          {props.data.description}
        </Text>
      ) : null}
    </Flex>
  </chakraComponents.Option>
);

export interface SelectProps {
  label?: string;
  labelProps?: FormLabelProps;
  placeholder?: string;
  tooltip?: string | null;
  options?: Option[] | [];
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
  isFormikOnChange?: boolean;
  isCustomOption?: boolean;
  textColor?: string;
}

export const SELECT_STYLES: ChakraStylesConfig<
  Option,
  boolean,
  GroupBase<Option>
> = {
  container: (provided) => ({
    ...provided,
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
};

export const SelectInput = ({
  options = [],
  fieldName,
  placeholder,
  size,
  isSearchable,
  isClearable,
  isMulti = false,
  singleValueBlock,
  isDisabled = false,
  menuPosition = "fixed",
  onChange,
  isCustomOption,
  textColor,
  ariaLabel,
  ariaLabelledby,
  ariaDescribedby,
}: {
  fieldName: string;
  isMulti?: boolean;
  onChange?: any;
  ariaLabel?: string;
  ariaLabelledby?: string;
  ariaDescribedby?: string;
} & Omit<SelectProps, "label">) => {
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
      newValue.map((v) => v.value),
    );
  };
  const handleChangeSingle = (newValue: SingleValue<Option>) => {
    if (newValue) {
      setFieldValue(fieldName, newValue.value);
    } else if (isClearable) {
      setFieldValue(fieldName, "");
    }
  };

  const handleChange = (newValue: MultiValue<Option> | SingleValue<Option>) => {
    if (onChange) {
      onChange(newValue);
    }
    if (isMulti) {
      handleChangeMulti(newValue as MultiValue<Option>);
    } else {
      handleChangeSingle(newValue as SingleValue<Option>);
    }
  };

  const components: SelectComponentsConfig<
    Option,
    boolean,
    GroupBase<Option>
  > = {};
  if (!isClearable) {
    components.ClearIndicator = ClearIndicator;
  }

  if (isCustomOption) {
    components.Option = CustomOption;
  }

  if (isDisabled) {
    // prevent the tags from being removed if the input is disabled
    components.MultiValueRemove = function CustomMultiValueRemove() {
      return null;
    };
  }

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
      placeholder={placeholder}
      focusBorderColor="primary.600"
      chakraStyles={{
        ...SELECT_STYLES,
        multiValueLabel: (provided) => ({
          ...provided,
          display: "flex",
          height: "16px",
          alignItems: "center",
          color: textColor,
        }),
        multiValue: (provided) => ({
          ...provided,
          fontWeight: "400",
          background: "gray.200",
          color: "gray.600",
          borderRadius: "2px",
          py: 1,
          px: 2,
        }),
        multiValueRemove: (provided) => ({
          ...provided,
          ml: 1,
          size: "lg",
          width: 3,
          height: 3,
        }),
        singleValue: singleValueBlock
          ? (provided) => ({
              ...provided,
              fontSize: "12px",
              background: "gray.200",
              color: textColor ?? "gray.600",
              fontWeight: "400",
              borderRadius: "2px",
              py: 1,
              px: 2,
            })
          : (provided) => ({ ...provided, color: textColor }),
      }}
      components={Object.keys(components).length > 0 ? components : undefined}
      isSearchable={isSearchable}
      isClearable={isClearable}
      instanceId={`select-${field.name}`}
      isMulti={isMulti}
      isDisabled={isDisabled}
      menuPosition={menuPosition}
      menuPlacement="auto"
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledby}
      aria-describedby={ariaDescribedby}
    />
  );
};

interface CreatableSelectProps extends SelectProps {
  /** Do not render the dropdown menu */
  disableMenu?: boolean;
}
const CreatableSelectInput = ({
  options = [],
  placeholder,
  fieldName,
  size,
  isSearchable,
  isClearable,
  isDisabled,
  isMulti,
  disableMenu,
  textColor,
  isCustomOption,
  singleValueBlock,
}: { fieldName: string } & Omit<CreatableSelectProps, "label">) => {
  const [initialField] = useField(fieldName);
  const value: string[] | string = initialField.value ?? [];
  const field = { ...initialField, value };
  const selected = Array.isArray(field.value)
    ? field.value.map((v) => ({ label: v, value: v }))
    : (options.find((o) => o.value === field.value) ?? {
        label: field.value,
        value: field.value,
      });

  const { setFieldValue, touched, setTouched } = useFormikContext();

  const handleChangeMulti = (newValue: MultiValue<Option>) => {
    setFieldValue(
      field.name,
      newValue.map((v) => v.value),
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

  const components: SelectComponentsConfig<
    Option,
    boolean,
    GroupBase<Option>
  > = {};
  const emptyComponent = () => null;

  if (disableMenu) {
    components.Menu = emptyComponent;
    components.DropdownIndicator = emptyComponent;
  }

  if (isCustomOption) {
    components.Option = CustomOption;
  }

  return (
    <CreatableSelect
      options={options}
      onBlur={(e) => {
        setTouched({ ...touched, [field.name]: true });
        field.onBlur(e);
      }}
      onChange={handleChange}
      name={fieldName}
      placeholder={placeholder}
      value={selected}
      size={size}
      classNamePrefix="custom-creatable-select"
      focusBorderColor="primary.600"
      isDisabled={isDisabled}
      chakraStyles={{
        container: (provided) => ({
          ...provided,
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
        multiValueLabel: (provided) => ({
          ...provided,
          display: "flex",
          height: "16px",
          alignItems: "center",
          color: textColor,
        }),
        multiValue: (provided) => ({
          ...provided,
          fontWeight: "400",
          background: "gray.200",
          color: "gray.600",
          borderRadius: "2px",
          py: 1,
          px: 2,
        }),
        multiValueRemove: (provided) => ({
          ...provided,
          ml: 1,
          size: "lg",
          width: 3,
          height: 3,
        }),
        singleValue: singleValueBlock
          ? (provided) => ({
              ...provided,
              fontSize: "12px",
              background: "gray.200",
              color: textColor ?? "gray.600",
              fontWeight: "400",
              borderRadius: "2px",
              py: 1,
              px: 2,
            })
          : (provided) => ({ ...provided, color: textColor }),
        option: (provided, { isSelected }) => ({
          ...provided,
          ...(isSelected && {
            background: "gray.200",
          }),
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
  inputRightElement,
  size,
  autoComplete,
  ...props
}: CustomInputProps & StringField) => {
  const [initialField, meta] = useField(props);
  const { type: initialType, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };

  const isPassword = initialType === "password";

  const innerInput = (
    <TextInput
      {...field}
      autoComplete={autoComplete}
      isDisabled={disabled}
      data-testid={`input-${field.name}`}
      placeholder={placeholder}
      isPassword={isPassword}
      inputRightElement={inputRightElement}
      size={size}
    />
  );

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns="1fr 3fr">
          {label ? (
            <Label htmlFor={props.id || props.name}>{label}</Label>
          ) : null}
          <Flex alignItems="center">
            <Flex flexDir="column" flexGrow={1} mr="2">
              {innerInput}
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
        {label ? (
          <Flex alignItems="center">
            <Label
              htmlFor={props.id || props.name}
              fontSize={size ?? "xs"}
              my={0}
              mr={1}
            >
              {label}
            </Label>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        ) : null}
        {innerInput}
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
  onChange,
  isFormikOnChange,
  isCustomOption,
  textColor,
  ...props
}: SelectProps & StringField) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns={label ? "1fr 3fr" : "1fr"}>
          {label ? (
            <Label htmlFor={props.id || props.name} {...labelProps}>
              {label}
            </Label>
          ) : null}
          <Flex alignItems="center" data-testid={`input-${field.name}`}>
            <Flex flexDir="column" flexGrow={1} mr={2}>
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
                isCustomOption={isCustomOption}
                singleValueBlock={singleValueBlock}
                menuPosition={props.menuPosition}
                onChange={!isFormikOnChange ? onChange : undefined}
                textColor={textColor}
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
          {label ? (
            <Label
              htmlFor={props.id || props.name}
              fontSize="xs"
              my={0}
              mr={1}
              {...labelProps}
            >
              {label}
            </Label>
          ) : null}
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
            isCustomOption={isCustomOption}
            menuPosition={props.menuPosition}
            onChange={!isFormikOnChange ? onChange : undefined}
            textColor={textColor}
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
  textColor,
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
            <Flex flexDir="column" flexGrow={1} mr={2}>
              <CreatableSelectInput
                fieldName={field.name}
                options={options}
                size={size}
                isSearchable={isSearchable}
                textColor={textColor}
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
          <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <Box width="100%" data-testid={`input-${field.name}`}>
          <CreatableSelectInput
            fieldName={field.name}
            options={options}
            size={size}
            isSearchable={isSearchable}
            textColor={textColor}
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
  isRequired?: boolean;
  resize?: boolean;
}
export const CustomTextArea = ({
  textAreaProps,
  label,
  tooltip,
  variant = "inline",
  isRequired = false,
  resize = false,
  ...props
}: CustomTextAreaProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resizeTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (resize && textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [resize]);

  const innerTextArea = (
    <Textarea
      size="sm"
      data-testid={`input-${field.name}`}
      {...field}
      {...textAreaProps}
      ref={textareaRef}
      style={{ overflowY: resize ? "hidden" : "visible" }}
      focusBorderColor="primary.600"
      onChange={(event) => {
        resizeTextarea();
        field.onChange(event);
      }}
    />
  );

  useEffect(() => {
    resizeTextarea(); // attempt to resize the textarea when the component mounts
  }, [resizeTextarea]);

  // When there is no label, it doesn't matter if stacked or inline
  // since we only render the text field
  if (!label) {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
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
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns="1fr 3fr">
          {label ? <FormLabel>{label}</FormLabel> : null}
          <Flex>
            <Flex flexDir="column" flexGrow={1} mr={2}>
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
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
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
  label?: string;
  options: Option[];
  variant?: "inline" | "stacked";
  defaultFirstSelected?: boolean;
}
export const CustomRadioGroup = ({
  label,
  options,
  variant,
  defaultFirstSelected = true,
  ...props
}: CustomRadioGroupProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);
  const defaultSelected = defaultFirstSelected ? options[0] : undefined;
  const selected =
    options.find((o) => o.value === field.value) ?? defaultSelected;

  const handleChange = (o: string) => {
    field.onChange(props.name)(o);
  };

  if (variant === "stacked") {
    return (
      <FormControl isInvalid={isInvalid}>
        <Stack width="fit-content">
          {label ? (
            <Label htmlFor={props.id || props.name}>{label}</Label>
          ) : null}
          <RadioGroup
            onChange={handleChange}
            value={selected?.value}
            data-testid={`input-${field.name}`}
            colorScheme="complimentary"
          >
            <Stack direction="column" spacing={3}>
              {options.map(
                ({ value, label: optionLabel, tooltip: optionTooltip }) => (
                  <Radio
                    key={value}
                    value={value}
                    data-testid={`option-${value}`}
                  >
                    <HStack alignItems="center" spacing={2}>
                      <Text fontSize="sm" fontWeight="medium">
                        {optionLabel}
                      </Text>
                      {optionTooltip ? (
                        <QuestionTooltip label={optionTooltip} />
                      ) : null}
                    </HStack>
                  </Radio>
                ),
              )}
            </Stack>
          </RadioGroup>
        </Stack>
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
      <Grid templateColumns="1fr 3fr">
        <Label htmlFor={props.id || props.name}>{label}</Label>
        <RadioGroup
          onChange={handleChange}
          value={selected?.value}
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

interface CustomNumberInputProps {
  label: string;
  tooltip?: string;
  variant?: "inline" | "condensed" | "stacked";
  isDisabled?: boolean;
  isRequired?: boolean;
  minValue?: number;
}
export const CustomNumberInput = ({
  label,
  tooltip,
  variant = "inline",
  isDisabled,
  isRequired = false,
  minValue,
  ...props
}: CustomNumberInputProps & FieldHookConfig<number>) => {
  const [field, meta] = useField({ ...props, type: "number" });
  const { setFieldValue } = useFormikContext();
  const isInvalid = !!(meta.touched && meta.error);

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns="1fr 3fr">
          <Label htmlFor={props.id || props.name}>{label}</Label>
          <Flex alignItems="center">
            <Flex flexDir="column" flexGrow={1} mr="2">
              <NumberInput focusBorderColor="primary.600">
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </Flex>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start" w="100%">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <NumberInput
          {...field}
          onChange={(e) => {
            if (
              minValue !== undefined &&
              (e as unknown as number) >= minValue
            ) {
              setFieldValue(props.name, e);
            }
          }}
          size="sm"
          w="100%"
          isDisabled={isDisabled}
          data-testid={`input-${field.name}`}
          min={minValue || undefined}
          focusBorderColor="primary.600"
        >
          <NumberInputField />
          <NumberInputStepper>
            <NumberIncrementStepper />
            <NumberDecrementStepper />
          </NumberInputStepper>
        </NumberInput>
      </VStack>
    </FormControl>
  );
};

interface CustomSwitchProps {
  label?: string;
  tooltip?: string;
  variant?: "inline" | "condensed" | "stacked" | "switchFirst";
  isDisabled?: boolean;
}
export const CustomSwitch = ({
  label,
  tooltip,
  variant = "inline",
  onChange,
  isDisabled,
  ...props
}: CustomSwitchProps & FieldHookConfig<boolean>) => {
  const [field, meta] = useField({ ...props, type: "checkbox" });
  const isInvalid = !!(meta.touched && meta.error);
  const innerSwitch = (
    <Field name={field.name}>
      {({ form: { setFieldValue } }: FieldProps) => (
        <Switch
          checked={field.checked}
          onChange={(v) => {
            setFieldValue(field.name, v);
          }}
          disabled={isDisabled}
          className="mr-2"
          data-testid={`input-${field.name}`}
          size="small"
        />
      )}
    </Field>
  );

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid}>
        <Grid templateColumns="1fr 3fr" justifyContent="center">
          <Label htmlFor={props.id || props.name} my={0}>
            {label}
          </Label>
          <Box display="flex" alignItems="center">
            {innerSwitch}
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Box>
        </Grid>
      </FormControl>
    );
  }

  if (variant === "switchFirst") {
    return (
      <FormControl isInvalid={isInvalid}>
        <Flex alignItems="center">
          {innerSwitch}
          <Label htmlFor={props.id || props.name} my={0} fontSize="sm" mr={2}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
      </FormControl>
    );
  }

  if (variant === "stacked") {
    return (
      <FormControl isInvalid={isInvalid} width="full">
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <HStack spacing={1}>
            <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={0}>
              {label}
            </Label>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </HStack>
          <HStack>{innerSwitch}</HStack>
        </Box>
      </FormControl>
    );
  }

  return (
    <FormControl isInvalid={isInvalid} width="fit-content">
      <Box display="flex" alignItems="center">
        <Label
          htmlFor={props.id || props.name}
          fontSize="sm"
          color="gray.500"
          my={0}
          mr={2}
        >
          {label}
        </Label>
        {innerSwitch}
        {tooltip ? <QuestionTooltip label={tooltip} /> : null}
      </Box>
    </FormControl>
  );
};

export const CustomCheckbox = ({
  label,
  tooltip,
  onChange,
  isDisabled,
  ...props
}: Omit<CustomSwitchProps, "variant"> & FieldHookConfig<boolean>) => {
  const [field, meta] = useField({ ...props, type: "checkbox" });
  const isInvalid = !!(meta.touched && meta.error);

  return (
    <FormControl isInvalid={isInvalid}>
      <Flex alignItems="center">
        <Checkbox
          name={field.name}
          isChecked={field.checked}
          onChange={field.onChange}
          onBlur={field.onBlur}
          data-testid={`input-${field.name}`}
          disabled={isDisabled}
          colorScheme="complimentary"
          mr="2"
        >
          <Text fontSize="sm" fontWeight="medium">
            {label}
          </Text>
        </Checkbox>

        {tooltip ? <QuestionTooltip label={tooltip} /> : null}
      </Flex>
    </FormControl>
  );
};

interface CustomClipboardCopyProps {
  label?: string;
  tooltip?: string;
  variant?: Variant;
}

export const CustomClipboardCopy = ({
  label,
  tooltip,
  variant = "inline",
  ...props
}: CustomClipboardCopyProps & StringField) => {
  const [initialField] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };

  const innerInput = (
    <Code
      display="flex"
      justifyContent="space-between"
      alignItems="center"
      p={0}
      width="100%"
    >
      <Text px={4}>{field.value}</Text>
      <ClipboardButton copyText={field.value} />
    </Code>
  );

  if (variant === "inline") {
    return (
      <FormControl>
        <Grid templateColumns="1fr 3fr">
          {label ? (
            <Label htmlFor={props.id || props.name}>{label}</Label>
          ) : null}
          <Flex alignItems="center">
            <Flex flexDir="column" flexGrow={1} mr="2">
              {innerInput}
            </Flex>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl>
      <VStack alignItems="start">
        {label ? (
          <Flex alignItems="center">
            <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
              {label}
            </Label>
            {tooltip ? <QuestionTooltip label={tooltip} /> : null}
          </Flex>
        ) : null}
        {innerInput}
      </VStack>
    </FormControl>
  );
};

interface CustomDatePickerProps {
  label?: string;
  name: string;
  tooltip?: string;
  isDisabled?: boolean;
  isRequired?: boolean;
  minValue?: string;
}

export const CustomDatePicker = ({
  label,
  name,
  tooltip,
  isDisabled,
  isRequired,
  minValue,
  ...props
}: CustomDatePickerProps & FieldHookConfig<Date>) => {
  const [field, meta, { setValue, setTouched }] = useField(name);
  const isInvalid = !!(meta.touched && meta.error);

  const { validateField } = useFormikContext();

  return (
    <FormControl isRequired={isRequired} isInvalid={isInvalid}>
      <VStack align="start">
        {!!label && (
          <Flex align="center">
            <Label htmlFor={props.id || name} fontSize="xs" my={0} mr={1}>
              {label}
            </Label>
            {!!tooltip && <QuestionTooltip label={tooltip} />}
          </Flex>
        )}
        <Input
          type="date"
          name={name}
          min={minValue}
          value={field.value}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            setValue(e.target.value);
            setTouched(true);
          }}
          onBlur={() => {
            validateField(name);
          }}
          size="sm"
          focusBorderColor="primary.600"
          data-testid={`input-${name}`}
          disabled={isDisabled}
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

export const CustomDateTimeInput = ({
  label,
  name,
  tooltip,
  disabled,
  isRequired,
  ...props
}: CustomInputProps & FieldHookConfig<string>) => {
  const [field, meta, { setValue, setTouched }] = useField(name);
  const isInvalid = !!(meta.touched && meta.error);

  const { validateField } = useFormikContext();

  const fieldId = props.id || name;

  return (
    <FormControl isRequired={isRequired} isInvalid={isInvalid}>
      <VStack align="start">
        {!!label && (
          <Flex align="center">
            <Label htmlFor={fieldId} fontSize="xs" my={0} mr={1}>
              {label}
            </Label>
            {!!tooltip && <QuestionTooltip label={tooltip} />}
          </Flex>
        )}
        <Input
          type="datetime-local"
          name={name}
          id={fieldId}
          value={field.value}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            setValue(e.target.value);
            setTouched(true);
          }}
          onBlur={() => {
            validateField(name);
          }}
          size="sm"
          focusBorderColor="primary.600"
          data-testid={`input-${name}`}
          isDisabled={disabled}
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
