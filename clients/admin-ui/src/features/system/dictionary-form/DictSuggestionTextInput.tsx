import { Flex, FormControl, Textarea, VStack } from "@fidesui/react";
import { useField, useFormikContext } from "formik";
import React, { useEffect, useState } from "react";

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
import { FormValues } from "~/features/system/form";

const useDictSuggestion = (fieldName: string, dictField: string) => {
  const [preSuggestionValue, setPreSuggestionValue] = useState("");
  const [initialField, meta, { setValue }] = useField(fieldName);
  const isInvalid = !!(meta.touched && meta.error);
  const { error } = meta;
  const field = { ...initialField, value: initialField.value ?? "" };
  const form = useFormikContext<FormValues>();

  const vendorId: string | undefined = form.values.meta?.vendor?.id;
  const dictEntry = useAppSelector(selectDictEntry(vendorId || ""));
  const isShowingSuggestions = useAppSelector(selectSuggestions);

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
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    isShowingSuggestions,
    setValue,
    dictEntry,
    dictField,
    setPreSuggestionValue,
  ]);

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
        <TextInput
          {...field}
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
