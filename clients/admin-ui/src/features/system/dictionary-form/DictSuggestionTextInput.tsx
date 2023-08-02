import { Flex, FormControl, VStack } from "@fidesui/react";
import {
  Formik,
  FormikConfig,
  FormikValues,
  useField,
  useFormikContext,
} from "formik";
import React, { createContext, useContext, useMemo, useState } from "react";

import { useAppDispatch,useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features/features.slice";
import {
  type CustomInputProps,
  ErrorMessage,
  Label,
  StringField,
  TextInput,
} from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { useGetAllDictionaryEntriesQuery } from "~/features/plus/plus.slice";
import { DictEntry } from "~/features/plus/types";
import {
  selectDictEntry,
  selectSuggestions,
  setSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";

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
  ...props
}: Props) => {
  const dispatch = useAppDispatch();
  const [preSuggestionValue, setPreSuggestionValue] = useState("");
  const [initialField, meta] = useField(props);
  const { type: initialType, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isPassword = initialType === "password";
  const form = useFormikContext();

  // @ts-ignore
  const vendorId = form.values?.meta?.vendor?.id;
  const dictEntry = useAppSelector(selectDictEntry(vendorId || ""));
  const isShowingSuggestions = useAppSelector(selectSuggestions);

  useMemo(() => {
    if (
      isShowingSuggestions === "showing" &&
      dictEntry &&
      dictField in dictEntry &&
      dictEntry[dictField as keyof typeof DictEntry]
    ) {
      if (field.value !== dictEntry[dictField]) {
        setPreSuggestionValue(field.value);
        form.setFieldValue(props.id, dictEntry[dictField]);
      }
    }
    if (isShowingSuggestions === "hiding") {
      form.setFieldValue(props.id, preSuggestionValue);
    }
    if (
      isShowingSuggestions === "reset" &&
      dictEntry &&
      dictField in dictEntry &&
      dictEntry[dictField as keyof typeof DictEntry]
    ) {
      form.setFieldValue(props.id, dictEntry[dictField]);
      dispatch(setSuggestions("showing"));
    }
  }, [isShowingSuggestions]);

  return (
    <FormControl isInvalid={isInvalid} isRequired={isRequired}>
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
          color={
            isShowingSuggestions === "showing"
              ? "complimentary.500"
              : "gray.800"
          }
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
