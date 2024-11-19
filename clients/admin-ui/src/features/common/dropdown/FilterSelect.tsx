import { AntSelect as Select, AntSelectProps as SelectProps } from "fidesui";

export const FilterSelect = <ValueType,>({
  ...props
}: SelectProps<ValueType>) => {
  const isMulti = props.mode === "multiple";
  return (
    <Select<ValueType>
      defaultActiveFirstOption={false}
      maxTagCount="responsive"
      allowClear
      dropdownStyle={isMulti ? undefined : { width: "auto", minWidth: "200px" }}
      {...props}
    />
  );
};
