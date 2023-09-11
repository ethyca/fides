import {
  Box,
  Flex,
  FormControl,
  HStack,
  Switch,
  Textarea,
  VStack,
} from "@fidesui/react";
import { MultiValue, Select, SingleValue } from "chakra-react-select";
import { useField, useFormikContext } from "formik";
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
import { DictEntry } from "~/features/plus/types";
import { selectSuggestions } from "~/features/system/dictionary-form/dict-suggestion.slice";
import type { FormValues } from "~/features/system/form";

const useDictSuggestion = (
  fieldName: string,
  dictField: string,
  fieldType?: string
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
    field.value ?? ""
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
    if (
      isShowingSuggestions === "showing" &&
      dictEntry &&
      dictField in dictEntry
    ) {
      if (field.value !== dictEntry[dictField as keyof DictEntry]) {
        setValue(dictEntry[dictField as keyof DictEntry]);

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
  }, [isShowingSuggestions, setValue, dictEntry, dictField, inputRef.current]);

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
  dictField: string;
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
  isRequired = false,
  dictField,
  name,
  id,
}: Props) => {
  const { field, isInvalid, isShowingSuggestions, error } = useDictSuggestion(
    name,
    dictField
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

export const DictSuggestionSwitch = ({
  label,
  tooltip,
  dictField,
  name,
  id,
}: Props) => {
  const { field, isInvalid, error } = useDictSuggestion(
    name,
    dictField,
    "checkbox"
  );
  return (
    <FormControl isInvalid={isInvalid} width="full">
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <HStack spacing={1}>
          <Label htmlFor={id || name} fontSize="sm" my={0} mr={0}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </HStack>
        <HStack>
          <Switch
            name={field.name}
            isChecked={field.checked}
            onChange={field.onChange}
            onBlur={field.onBlur}
            colorScheme="purple"
            mr={2}
            data-testid={`input-${field.name}`}
            size="sm"
          />
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

interface SelectOption {
  value: string;
  label: string;
}

type SelectProps = Props & {
  options: SelectOption[];
  isMulti?: boolean;
};

export const DictSuggestionSelect = ({
  label,
  tooltip,
  disabled,
  isRequired = false,
  dictField,
  name,
  placeholder,
  id,
  options,
  isMulti = false,
}: SelectProps) => {
  const { field, isInvalid, isShowingSuggestions, error } = useDictSuggestion(
    name,
    dictField
  );

  const selected = isMulti
    ? options.filter((o) => field.value.indexOf(o.value) >= 0)
    : options.find((o) => o.value === field.value) || null;

  const { setFieldValue } = useFormikContext();

  const handleChangeMulti = (newValue: MultiValue<SelectOption>) => {
    setFieldValue(
      field.name,
      newValue.map((v) => v.value)
    );
  };

  const handleChangeSingle = (newValue: SingleValue<SelectOption>) => {
    setFieldValue(field.name, newValue);
  };

  const handleChange = (
    newValue: MultiValue<SelectOption> | SingleValue<SelectOption>
  ) =>
    isMulti
      ? handleChangeMulti(newValue as MultiValue<SelectOption>)
      : handleChangeSingle(newValue as SingleValue<SelectOption>);

  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={id || name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <Flex width="100%">
          <Select
            {...field}
            size="sm"
            value={selected}
            isDisabled={disabled}
            isMulti={isMulti}
            onChange={handleChange}
            data-testid={`input-${field.name}`}
            placeholder={placeholder}
            options={options}
            chakraStyles={{
              input: (provided) => ({
                ...provided,
                color:
                  isShowingSuggestions === "showing"
                    ? "complimentary.500"
                    : "gray.800",
              }),
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
              }),
              multiValue: (provided) => ({
                ...provided,
                fontWeight: "400",
                background: "gray.200",
                color:
                  isShowingSuggestions === "showing"
                    ? "complimentary.500"
                    : "gray.800",
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
            }}
          />
        </Flex>
        <ErrorMessage
          isInvalid={isInvalid}
          message={error}
          fieldName={field.name}
        />
      </VStack>
    </FormControl>
  );
};
