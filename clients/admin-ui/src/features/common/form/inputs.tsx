/**
 * Various common form inputs, styled specifically for Formik forms used throughout our app
 */

import {
  Button,
  ChakraBox as Box,
  ChakraCode as Code,
  ChakraFlex,
  ChakraFormControl as FormControl,
  ChakraFormErrorMessage as FormErrorMessage,
  ChakraFormErrorMessageProps as FormErrorMessageProps,
  ChakraFormLabel as FormLabel,
  ChakraFormLabelProps as FormLabelProps,
  chakraForwardRef as forwardRef,
  ChakraGrid as Grid,
  ChakraHStack as HStack,
  ChakraInput as Input,
  ChakraInputGroup as InputGroup,
  ChakraInputProps as InputProps,
  ChakraInputRightElement as InputRightElement,
  ChakraText as Text,
  ChakraTextarea as Textarea,
  ChakraTextareaProps as TextareaProps,
  ChakraVStack as VStack,
  DefaultOptionType,
  EyeIcon,
  Flex,
  Switch,
  SwitchProps,
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
import { InfoTooltip } from "~/features/common/InfoTooltip";

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

/**
 * @deprecated in favor of Form.Input label prop
 */
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
      isEditing,
      isEditPassword,
      handleClickEdit,
      handleClickUndo,
      ...props
    }: InputProps & {
      isPassword: boolean;
      isEditPassword?: boolean;
      isEditing?: boolean;
      inputRightElement?: React.ReactNode;
      handleClickUndo?: () => void;
      handleClickEdit?: () => void;
    },
    ref,
  ) => {
    const [type, setType] = useState<"text" | "password">(
      isPassword ? "password" : "text",
    );

    const handleClickReveal = () =>
      setType(type === "password" ? "text" : "password");

    return (
      <Flex className="w-full" gap="small" justify="center" align="center">
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
          {isPassword && (!isEditPassword || !!isEditing) && (
            <InputRightElement pr="2">
              <Button
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
          )}
        </InputGroup>
        {isEditPassword && (
          <Button
            onClick={isEditing ? handleClickUndo : handleClickEdit}
            aria-label={`${isEditing ? "Restore" : "Edit"} Secret`}
          >
            {isEditing ? "Undo" : "Edit"}
          </Button>
        )}
      </Flex>
    );
  },
);
TextInput.displayName = "TextInput";

/**
 * @deprecated in favor of Form.Input with the appropriate status and help props
 */
export const ErrorMessage = ({
  isInvalid,
  message,
  fieldName,
  ...props
}: {
  isInvalid: boolean;
  fieldName: string;
  message?: string;
} & FormErrorMessageProps) => {
  if (!isInvalid) {
    return null;
  }
  return (
    <FormErrorMessage data-testid={`error-${fieldName}`} {...props}>
      {message}
    </FormErrorMessage>
  );
};

export interface Option extends DefaultOptionType {
  value: string;
  label: string;
  description?: string | null;
  tooltip?: string;
}

export const CustomTextInput = ({
  label,
  tooltip,
  disabled,
  variant = "inline",
  isRequired = false,
  inputRightElement,
  size,
  autoComplete,
  autoFocus,
  ...props
}: CustomInputProps & StringField) => {
  const [initialField, meta, helpers] = useField(props);
  const { type: initialType, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isPassword = initialType === "password";
  const isEditPassword = isPassword && !!meta.initialValue;

  const [isDisabled, setIsDisabled] = useState(
    disabled || (isPassword && !!isEditPassword),
  );

  const handleClickEdit = () => {
    helpers.setValue(undefined);
    setIsDisabled(false);
  };

  const handleClickUndo = () => {
    helpers.setValue(meta.initialValue);
    setIsDisabled(true);
  };

  useEffect(() => {
    if (isEditPassword) {
      return;
    }

    setIsDisabled(!!disabled);
  }, [disabled, isEditPassword, setIsDisabled]);

  const innerInput = (
    <TextInput
      {...field}
      id={props.id || props.name}
      autoComplete={autoComplete}
      autoFocus={autoFocus}
      isDisabled={isDisabled}
      data-testid={`input-${field.name}`}
      placeholder={placeholder}
      isPassword={isPassword}
      isEditPassword={isEditPassword}
      isEditing={!isDisabled}
      inputRightElement={inputRightElement}
      handleClickEdit={handleClickEdit}
      handleClickUndo={handleClickUndo}
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
          <ChakraFlex alignItems="center">
            <ChakraFlex flexDir="column" flexGrow={1} mr="2">
              {innerInput}
              <ErrorMessage
                isInvalid={isInvalid}
                message={meta.error}
                fieldName={field.name}
              />
            </ChakraFlex>
            <InfoTooltip
              label={tooltip}
              className={isInvalid ? "mt-2 self-start" : undefined}
            />
          </ChakraFlex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start">
        {label ? (
          <ChakraFlex alignItems="center">
            <Label
              htmlFor={props.id || props.name}
              fontSize={size ?? "xs"}
              my={0}
              mr={1}
            >
              {label}
            </Label>
            <InfoTooltip label={tooltip} />
          </ChakraFlex>
        ) : null}
        {innerInput}
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
          mt={0}
          fontSize={size ?? "xs"}
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
        <ChakraFlex>
          <ChakraFlex flexDir="column" flexGrow={1}>
            {innerTextArea}
            <ErrorMessage
              isInvalid={isInvalid}
              message={meta.error}
              fieldName={field.name}
            />
          </ChakraFlex>
          <InfoTooltip label={tooltip} />
        </ChakraFlex>
      </FormControl>
    );
  }

  if (variant === "inline") {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns="1fr 3fr">
          {label ? <FormLabel>{label}</FormLabel> : null}
          <ChakraFlex>
            <ChakraFlex flexDir="column" flexGrow={1} mr={2}>
              {innerTextArea}
              <ErrorMessage
                isInvalid={isInvalid}
                message={meta.error}
                fieldName={field.name}
              />
            </ChakraFlex>
            <InfoTooltip label={tooltip} />
          </ChakraFlex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start">
        <ChakraFlex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          <InfoTooltip label={tooltip} />
        </ChakraFlex>
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

interface CustomSwitchProps {
  label?: string;
  tooltip?: string;
  variant?: "inline" | "condensed" | "stacked" | "switchFirst";
  size?: SwitchProps["size"];
  isDisabled?: boolean;
  onChange?: (checked: boolean) => void;
  className?: string;
  /**
   * When provided, the switch will render with this checked state instead of the Formik-managed value.
   * Useful for read-only or UI-only switches that shouldn't be toggleable.
   */
  checkedOverride?: boolean;
}
export const CustomSwitch = ({
  label,
  tooltip,
  variant = "inline",
  size = "small",
  onChange,
  isDisabled,
  checkedOverride,
  ...props
}: CustomSwitchProps & Omit<FieldHookConfig<boolean>, "onChange">) => {
  const [field, meta] = useField({
    name: props.name,
    value: props.value,
    type: "checkbox",
  });
  const isInvalid = !!(meta.touched && meta.error);
  const innerSwitch = (
    <Field name={field.name}>
      {({ form: { setFieldValue } }: FieldProps) => (
        <Switch
          checked={checkedOverride ?? field.checked}
          onChange={(v) => {
            setFieldValue(field.name, v);
            onChange?.(v);
          }}
          disabled={isDisabled}
          className="mr-2"
          data-testid={`input-${field.name}`}
          size={size}
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
            <InfoTooltip label={tooltip} />
          </Box>
        </Grid>
      </FormControl>
    );
  }

  if (variant === "switchFirst") {
    return (
      <FormControl isInvalid={isInvalid}>
        <ChakraFlex alignItems="center">
          {innerSwitch}
          <Label htmlFor={props.id || props.name} my={0} fontSize="sm" mr={2}>
            {label}
          </Label>
          <InfoTooltip label={tooltip} />
        </ChakraFlex>
      </FormControl>
    );
  }

  if (variant === "stacked") {
    return (
      <FormControl isInvalid={isInvalid} width="full">
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <HStack spacing={1} mr={1}>
            <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={0}>
              {label}
            </Label>
            <InfoTooltip label={tooltip} />
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
        <InfoTooltip label={tooltip} />
      </Box>
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
          <ChakraFlex alignItems="center">
            <ChakraFlex flexDir="column" flexGrow={1} mr="2">
              {innerInput}
            </ChakraFlex>
            <InfoTooltip label={tooltip} />
          </ChakraFlex>
        </Grid>
      </FormControl>
    );
  }
  return (
    <FormControl>
      <VStack alignItems="start">
        {label ? (
          <ChakraFlex alignItems="center">
            <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
              {label}
            </Label>
            <InfoTooltip label={tooltip} />
          </ChakraFlex>
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
          <ChakraFlex align="center">
            <Label htmlFor={props.id || name} fontSize="xs" my={0} mr={1}>
              {label}
            </Label>
            {!!tooltip && <InfoTooltip label={tooltip} />}
          </ChakraFlex>
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

/**
 * @deprecated in favor of FormikDateTimeInput
 */
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
          <ChakraFlex align="center">
            <Label htmlFor={fieldId} fontSize="xs" my={0} mr={1}>
              {label}
            </Label>
            {!!tooltip && <InfoTooltip label={tooltip} />}
          </ChakraFlex>
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
