import { Flex, FormControl, Textarea, VStack } from "@fidesui/react";
import { useField, useFormikContext } from "formik";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { MultiValue, Select, SingleValue } from "chakra-react-select";

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
  const [initialField, meta, { setValue }] = useField(fieldName);
  const isInvalid = !!(meta.touched && meta.error);
  const { error } = meta;
  const field = { ...initialField, value: initialField.value ?? "" };
  const form = useFormikContext();
  const context = useResetSuggestionContext();
  // @ts-ignore
  const vendorId = form.values?.meta?.vendor?.id;
  const dictEntry = useAppSelector(selectDictEntry(vendorId || ""));
  const isShowingSuggestions = useAppSelector(selectSuggestions);

  useMemo(() => console.log(dictEntry), [dictEntry]);

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
        if (
          field.name === "legal_basis_for_profiling" ||
          field.name === "legal_basis_for_transfers"
        ) {
          //@ts-ignore
          setValue(dictEntry[dictField as keyof DictEntry][0]);
        }
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

  const reset = useCallback(() => {
    if (dictEntry && dictField in dictEntry) {
      setValue(dictEntry[dictField as keyof DictEntry], true);
    }
  }, [dictEntry, dictField, setValue]);

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

interface SelectOption {
  value: string;
  label: string;
}

type SelectProps = Props & {
  options: SelectOption[];
  isMulti?: boolean;
};

// export const DictSuggestionSelect = ({
//   label,
//   tooltip,
//   disabled,
//   isRequired = false,
//   dictField,
//   name,
//   placeholder,
//   id,
//   options,
// }: SelectProps) => {
//   const { field, isInvalid, isShowingSuggestions, error } = useDictSuggestion(
//     name,
//     dictField
//   );

//   return (
//     <FormControl isInvalid={isInvalid} isRequired={isRequired}>
//       <VStack alignItems="start">
//         <Flex alignItems="center">
//           <Label htmlFor={id || name} fontSize="xs" my={0} mr={1}>
//             {label}
//           </Label>
//           {tooltip ? <QuestionTooltip label={tooltip} /> : null}
//         </Flex>
//         <TextInput
//           {...field}
//           isDisabled={disabled}
//           data-testid={`input-${field.name}`}
//           placeholder={placeholder}
//           isPassword={false}
//           color={
//             isShowingSuggestions === "showing"
//               ? "complimentary.500"
//               : "gray.800"
//           }
//         />
//         <ErrorMessage
//           isInvalid={isInvalid}
//           message={error}
//           fieldName={field.name}
//         />
//       </VStack>
//     </FormControl>
//   );
// };

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
    // console.log(newValue);
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
  ) => {
    isMulti
      ? handleChangeMulti(newValue as MultiValue<SelectOption>)
      : handleChangeSingle(newValue as SingleValue<SelectOption>);
  };

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
            onChange={(e) => {
              handleChange(e);
            }}
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
