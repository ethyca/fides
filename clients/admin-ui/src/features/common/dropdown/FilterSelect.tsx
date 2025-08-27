import { AntSelect as Select, AntSelectProps as SelectProps } from "fidesui";

export const FilterSelect = ({ ...props }: SelectProps) => (
  <Select
    defaultActiveFirstOption={false}
    maxTagCount="responsive"
    allowClear
    styles={
      props.mode
        ? undefined
        : {
            popup: { root: { width: "auto", minWidth: "200px" } },
          }
    }
    className="w-auto"
    data-testid="filter-select"
    {...props}
  />
);
