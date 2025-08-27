import {
  AntDefaultOptionType,
  AntFlex,
  AntSelect,
  FormControl,
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
      const newValue = uniq([...suggestedDataUses, ...value]);
      setValue(newValue);
    } else {
      setValue(value);
    }
  };

  const optionsGroups = useMemo(() => {
    const suggestedOptions: AntDefaultOptionType[] = [];
    const allOptions: AntDefaultOptionType[] = [];
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

  return (
    <FormControl isInvalid={isInvalid}>
      <AntFlex vertical gap="small">
        <AntFlex align="center">
          <Label htmlFor={props.id || name} fontSize="xs" my={0} mr={1}>
            Data uses
          </Label>
        </AntFlex>
        <AntSelect
          options={[
            {
              label: "Select all suggested",
              value: ALL_SUGGESTED_VALUE,
            },
            {
              label: (
                <AntFlex gap="small" align="center">
                  <SparkleIcon />
                  <strong>Suggested data uses</strong>
                </AntFlex>
              ),
              value: "suggested",
              options: optionsGroups.suggested,
            },
            {
              label: (
                <AntFlex gap="small" align="center">
                  <Icons.Document />
                  <strong>All data uses</strong>
                </AntFlex>
              ),
              value: "all",
              options: optionsGroups.all,
            },
          ]}
          mode="multiple"
          placeholder="Select data uses"
          allowClear
          loading={loading}
          value={field.value}
          onChange={onChange}
          popupRender={(menu) => {
            return <div>{menu}</div>;
          }}
          status={isInvalid ? "error" : undefined}
          virtual={false}
          {...props}
        />
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
        />
      </AntFlex>
    </FormControl>
  );
};

export default DataUseSelectWithSuggestions;
