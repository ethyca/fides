import { AntSelect as Select, AntSelectProps as SelectProps } from "fidesui";

import { useGetAllSystemGroupsQuery } from "~/features/system/system-groups.slice";

const SystemGroupSelect = (props: SelectProps) => {
  const { data: systemGroups } = useGetAllSystemGroupsQuery();

  const options = systemGroups?.map((group) => ({
    value: group.fides_key,
    label: group.name,
  }));

  // eslint-disable-next-line jsx-a11y/control-has-associated-label
  return (
    <Select options={options} placeholder="Select a system group" {...props} />
  );
};

export default SystemGroupSelect;
