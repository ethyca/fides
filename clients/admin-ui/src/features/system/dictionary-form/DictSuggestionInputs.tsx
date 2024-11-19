import {
  AntSwitch as Switch,
  Box,
  Flex,
  FormControl,
  HStack,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Textarea,
  VStack,
} from "fidesui";
import { Field, FieldProps, useField, useFormikContext } from "formik";
import React, { useEffect, useRef, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  type CustomInputProps,
  ErrorMessage,
  Label,
  StringField,
  TextInput,
} from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { selectDictEntry } from "~/features/plus/plus.slice";
import { selectSuggestions } from "~/features/system/dictionary-form/dict-suggestion.slice";
import type { FormValues } from "~/features/system/form";
import { Vendor } from "~/types/dictionary-api";

const useDictSuggestion = (
  fieldName: string,
  dictField?: (vendor: Vendor) => string | boolean,
  fieldType?: string,
) => {
  const [initialField, meta, { setValue, setTouched }] = useField({
    name: fieldName,
    type: fieldType || undefined,
  });
  const isInvalid = !!(meta.touched && meta.error);
  const { error } = meta;
  const field = {
    ...initialField,
    value: initialField.value ?? "",
  };

  const [preSuggestionValue, setPreSuggestionValue] = useState(
    field.value ?? "",
  );
  const { values } = useFormikContext<FormValues>();
  const { vendor_id: vendorId } = values;
  const dictEntry = useAppSelector(selectDictEntry(vendorId || ""));
  const isShowingSuggestions = useAppSelector(selectSuggestions);
  const inputRef = useRef();

  useEffect(() => {
    if (isShowingSuggestions === "showing") {
      setPreSuggestionValue(field.value);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isShowingSuggestions, setPreSuggestionValue]);

  useEffect(() => {
    if (isShowingSuggestions === "showing" && dictEntry) {
      // Either use the passed in getter for a dictfield, or default to the field name
      const dictFieldValue = dictField
        ? dictField(dictEntry)
        : dictEntry[fieldName as keyof Vendor];
      if (field.value !== dictFieldValue) {
        setValue(dictFieldValue);

        // This blur is a workaround some forik issues.
        // the setTimeout is required to get around a
        // timing issue with the ref not being ready yet.
        setTimeout(() => {
          setTouched(true);
          // @ts-ignore
          inputRef.current?.blur();
        }, 300);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isShowingSuggestions, setValue, dictEntry, inputRef.current]);

  useEffect(() => {
    if (isShowingSuggestions === "hiding") {
      setValue(preSuggestionValue);
    }
  }, [isShowingSuggestions, setValue, preSuggestionValue]);

  return {
    field,
    isInvalid,
    isShowingSuggestions,
    error,
    inputRef,
  };
};

type Props = {
  dictField?: (vendor: Vendor) => string | boolean;
} & Omit<CustomInputProps, "variant"> &
  StringField;

export const DictSuggestionTextInput = ({
  label,
  tooltip,
  disabled,
  isRequired = false,
  dictField,
  name,
  placeholder,
  id,
}: Props) => {
  const { field, isInvalid, isShowingSuggestions, error, inputRef } =
    useDictSuggestion(name, dictField);

  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={id || name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <TextInput
          {...field}
          ref={inputRef}
          isRequired={isRequired}
          isDisabled={disabled}
          data-testid={`input-${field.name}`}
          placeholder={placeholder}
          isPassword={false}
          color={
            isShowingSuggestions === "showing"
              ? "complimentary.500"
              : "gray.800"
          }
        />
        <ErrorMessage
          isInvalid={isInvalid}
          message={error}
          fieldName={field.name}
        />
      </VStack>
    </FormControl>
  );
};

export const DictSuggestionTextArea = ({
  label,
  tooltip,
  disabled,
  isRequired = false,
  dictField,
  name,
  id,
}: Props) => {
  const { field, isInvalid, isShowingSuggestions, error } = useDictSuggestion(
    name,
    dictField,
  );

  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={id || name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>

        <Textarea
          {...field}
          size="sm"
          data-testid={`input-${field.name}`}
          focusBorderColor="primary.600"
          color={
            isShowingSuggestions === "showing"
              ? "complimentary.500"
              : "gray.800"
          }
          isDisabled={disabled}
        />
        <ErrorMessage
          isInvalid={isInvalid}
          message={error}
          fieldName={field.name}
        />
      </VStack>
    </FormControl>
  );
};

export const DictSuggestionSwitch = ({
  label,
  tooltip,
  dictField,
  name,
  id,
  disabled,
}: Props) => {
  const { field, isInvalid, error } = useDictSuggestion(
    name,
    dictField,
    "checkbox",
  );
  return (
    <FormControl isInvalid={isInvalid} width="full">
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <HStack spacing={1}>
          <Label htmlFor={id || name} fontSize="xs" my={0} mr={0}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </HStack>
        <HStack>
          <Field name={field.name}>
            {({ form: { setFieldValue } }: FieldProps) => (
              <Switch
                checked={field.checked}
                onChange={(v) => {
                  setFieldValue(field.name, v);
                }}
                disabled={disabled}
                className="mr-2"
                data-testid={`input-${field.name}`}
                size="small"
              />
            )}
          </Field>
        </HStack>
      </Box>
      <ErrorMessage
        isInvalid={isInvalid}
        message={error}
        fieldName={field.name}
      />
    </FormControl>
  );
};

export const DictSuggestionNumberInput = ({
  label,
  tooltip,
  dictField,
  name,
  id,
  disabled,
}: Props) => {
  const { field, isInvalid, error, isShowingSuggestions } = useDictSuggestion(
    name,
    dictField,
    "numeric",
  );

  const { setFieldValue } = useFormikContext();

  return (
    <FormControl isInvalid={isInvalid} width="full">
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <HStack spacing={1}>
          <Label htmlFor={id || name} fontSize="xs" my={0} mr={0}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </HStack>
        <HStack>
          <NumberInput
            value={field.value}
            name={field.name}
            size="xs"
            onBlur={field.onBlur}
            onChange={(v) => {
              setFieldValue(field.name, v);
            }}
            w="100%"
            colorScheme="purple"
            inputMode="numeric"
            data-testid={`input-${field.name}`}
            color={
              isShowingSuggestions === "showing"
                ? "complimentary.500"
                : "gray.800"
            }
            focusBorderColor="primary.600"
            isDisabled={disabled}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </HStack>
      </Box>
      <ErrorMessage
        isInvalid={isInvalid}
        message={error}
        fieldName={field.name}
      />
    </FormControl>
  );
};
