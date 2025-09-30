import {
  AntDefaultOptionType as DefaultOptionType,
  AntFlex as Flex,
  AntSelect as Select,
  AntSpace as Space,
  Icons,
  SparkleIcon,
} from "fidesui";
import { useField } from "formik";
import { uniq } from "lodash";
import { useMemo } from "react";

import { ControlledSelectProps } from "~/features/common/form/ControlledSelect";
import { ErrorMessage, Label } from "~/features/common/form/inputs";

const ALL_SUGGESTED_VALUE = "all-suggested";

const DataUseSelectWithSuggestions = ({
  options,
  loading,
  name,
  suggestedDataUses,
  ...props
}: ControlledSelectProps & { suggestedDataUses: string[] }) => {
  const [field, meta, { setValue }] = useField(name);
  const isInvalid = !!(meta.touched && meta.error);

  const onChange = (value: string[]) => {
    if (value.includes(ALL_SUGGESTED_VALUE)) {
      const newValue = uniq([
        ...suggestedDataUses,
        ...value.filter((v) => v !== ALL_SUGGESTED_VALUE),
      ]);
      setValue(newValue);
    } else {
      setValue(value);
    }
  };

  const optionsGroups = useMemo(() => {
    const suggestedOptions: DefaultOptionType[] = [];
    const allOptions: DefaultOptionType[] = [];
    options?.forEach((opt) => {
      if (suggestedDataUses.includes(opt.value as string)) {
        suggestedOptions.push(opt);
      } else {
        allOptions.push(opt);
      }
    });
    return {
      suggested: suggestedOptions,
      all: allOptions,
    };
  }, [options, suggestedDataUses]);

  const optionsToRender = optionsGroups.suggested.length
    ? [
        {
          label: "Select all suggested",
          value: ALL_SUGGESTED_VALUE,
        },
        {
          label: (
            <Space>
              <SparkleIcon size={14} />
              <span>Suggested data uses</span>
            </Space>
          ),
          value: "suggested",
          options: optionsGroups.suggested,
        },
        {
          label: (
            <Space>
              <Icons.Document />
              <span>All data uses</span>
            </Space>
          ),
          value: "all",
          options: optionsGroups.all,
        },
      ]
    : optionsGroups.all;

  return (
    <Flex vertical gap="small">
      <Flex align="center">
        <Label htmlFor={props.id || name} fontSize="xs" my={0} mr={1}>
          Data uses
        </Label>
      </Flex>
      <Select
        options={optionsToRender}
        mode="multiple"
        placeholder="Select data uses"
        allowClear
        loading={loading}
        value={field.value}
        onChange={onChange}
        status={isInvalid ? "error" : undefined}
        virtual={false}
        {...props}
      />
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
    </Flex>
  );
};

export default DataUseSelectWithSuggestions;
