import { Flex, FormControl, Textarea, VStack } from "@fidesui/react";
import { useField, useFormikContext } from "formik";
import React, { useCallback, useEffect, useRef, useState } from "react";

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

import { useResetSuggestionContext } from "./dict-suggestion.context";

const useDictSuggestion = (fieldName: string, dictField: string) => {
  const [preSuggestionValue, setPreSuggestionValue] = useState("");
  const [initialField, meta, { setValue, setTouched }] = useField(fieldName);
  const isInvalid = !!(meta.touched && meta.error);
  const { error } = meta;
  const field = { ...initialField, value: initialField.value ?? "" };
  const {
    values,
    touched,
  } = useFormikContext();
  const context = useResetSuggestionContext();
  // @ts-ignore
  const vendorId = values?.meta?.vendor?.id;
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

        setTimeout(() => {
          setTouched(true);
          // @ts-ignore
          inputRef.current?.blur();
        }, 300);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    isShowingSuggestions,
    setValue,
    dictEntry,
    dictField,
    inputRef.current,
  ]);

  useEffect(() => {
    if (isShowingSuggestions === "hiding") {
      setValue(preSuggestionValue);
    }
  }, [isShowingSuggestions, setValue, preSuggestionValue]);

  const reset = useCallback(() => {
    if (dictEntry && dictField in dictEntry) {
      setValue(dictEntry[dictField as keyof DictEntry]);
      setTouched(true, true);
    }
  }, [dictEntry, dictField, setValue, setTouched]);

  useEffect(() => {
    if (context) {
      const payload = {
        name: fieldName,
        callback: reset,
      };
      context.addResetCallback(payload);
    }
    return () => {
      if (context) {
        context.removeResetCallback(fieldName);
      }
    };
  }, [context, reset, fieldName]);

  return {
    field,
    isInvalid,
    isShowingSuggestions,
    error,
    touched,
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
