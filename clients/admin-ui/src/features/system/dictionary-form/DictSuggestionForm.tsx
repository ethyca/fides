import React, { createContext, useContext } from "react";
import {
  Formik,
  FormikValues,
  FormikConfig,
  useField,
  useFormikContext,
} from "formik";
import { useGetAllDictionaryEntriesQuery } from "~/features/plus/plus.slice";
import { useFeatures } from "~/features/common/features/features.slice";
import { Flex, FormControl, VStack } from "@fidesui/react";
import {
  Label,
  ErrorMessage,
  StringField,
  TextInput,
  type CustomInputProps,
} from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { useAppSelector } from "~/app/hooks";
import { selectDictEntry } from "~/features/system/dictionary-form/dict-suggestion.slice";

export const DictSuggestionTextInput = ({
  label,
  tooltip,
  disabled,
  isRequired = false,
  ...props
}: CustomInputProps & StringField) => {
  const [initialField, meta] = useField(props);
  const { type: initialType, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isPassword = initialType === "password";
  const form = useFormikContext();
  const dictEntry = useAppSelector(
    selectDictEntry(form.values?.meta?.vendor?.id || "")
  );

  console.log("loaded dict entry", dictEntry);
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
