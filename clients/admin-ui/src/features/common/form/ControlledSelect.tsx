import type { FormLabelProps } from "fidesui";
import {
  AntFlex as Flex,
  AntSelect as Select,
  AntSelectProps as SelectProps,
  FormControl,
  Grid,
  VStack,
} from "fidesui";
import { useField } from "formik";
import { useState } from "react";

import QuestionTooltip from "../QuestionTooltip";
import { ErrorMessage, Label } from "./inputs";

interface ControlledSelectProps extends SelectProps {
  name: string;
  label?: string;
  labelProps?: FormLabelProps;
  tooltip?: string | null;
  isRequired?: boolean;
  layout?: "inline" | "stacked";
}

export const ControlledSelect = ({
  name,
  label,
  labelProps,
  tooltip,
  isRequired,
  layout = "inline",
  ...props
}: ControlledSelectProps) => {
  const [field, meta, { setValue }] = useField(name);
  const isInvalid = !!(meta.touched && meta.error);
  const [searchValue, setSearchValue] = useState("");

  if (!field.value && (props.mode === "tags" || props.mode === "multiple")) {
    field.value = [];
  }
  if (props.mode === "tags" && typeof field.value === "string") {
    field.value = [field.value];
  }

  // Tags mode requires a custom option, everything else should just pass along the props or undefined
  const optionRender =
    props.mode === "tags"
      ? (option: any, info: any) => {
          if (!option) {
            return undefined;
          }
          if (
            option.value === searchValue &&
            !field.value.includes(searchValue)
          ) {
            return `Create "${searchValue}"`;
          }
          if (props.optionRender) {
            return props.optionRender(option, info);
          }
          return option.label;
        }
      : props.optionRender || undefined;

  // this just supports the custom tag option, otherwise it's completely unnecessary
  const handleSearch = (value: string) => {
    setSearchValue(value);
    if (props.onSearch) {
      props.onSearch(value);
    }
  };

  // Pass the value to the formik field
  const handleChange = (newValue: any, option: any) => {
    setValue(newValue);
    if (props.onChange) {
      props.onChange(newValue, option);
    }
  };

  if (layout === "inline") {
    return (
      <FormControl isInvalid={isInvalid} isRequired={isRequired}>
        <Grid templateColumns={label ? "1fr 3fr" : "1fr"}>
          {label ? (
            <Label htmlFor={props.id || name} {...labelProps}>
              {label}
            </Label>
          ) : null}
          <Flex align="center">
            <Flex vertical flex={1} className="mr-2">
              <Select
                {...field}
                id={props.id || name}
                data-testid={`controlled-select-${field.name}`}
                {...props}
                optionRender={optionRender}
                onSearch={props.mode === "tags" ? handleSearch : undefined}
                onChange={handleChange}
                value={field.value || undefined} // solves weird bug where placeholder won't appear if value is an empty string ""
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
        <Flex align="center">
          {label ? (
            <Label
              htmlFor={props.id || name}
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
        <Select
          {...field}
          id={props.id || name}
          data-testid={`controlled-select-${field.name}`}
          {...props}
          optionRender={optionRender}
          onSearch={props.mode === "tags" ? handleSearch : undefined}
          onChange={handleChange}
          value={field.value || undefined} // solves weird bug where placeholder won't appear if value is an empty string ""
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
