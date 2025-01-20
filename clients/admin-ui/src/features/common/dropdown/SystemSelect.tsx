import { AntSelect as Select, AntSelectProps as SelectProps } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { useGetSystemsQuery } from "~/features/system/system.slice";

import { debounce } from "../utils";

const OPTIONS_LIMIT = 25;

interface SystemSelectProps
  extends Omit<
    SelectProps,
    "options" | "showSearch" | "filterOption" | "onSearch"
  > {}

export const SystemSelect = ({ ...props }: SystemSelectProps) => {
  const [searchValue, setSearchValue] = useState<string>();
  const { data, isFetching } = useGetSystemsQuery({
    page: 1,
    size: OPTIONS_LIMIT,
    search: searchValue || undefined,
  });

  const options = data?.items?.map((system) => ({
    value: system.fides_key,
    label: system.name,
  }));

  const handleSearch = useCallback(
    (search: string) => {
      if (search?.length > 1) {
        setSearchValue(search);
      }
      if (search?.length === 0) {
        setSearchValue(undefined);
      }
    },
    [setSearchValue],
  );

  const onSearch = useMemo(() => debounce(handleSearch, 300), [handleSearch]);

  return (
    <Select
      placeholder="Search..."
      aria-label="Search for a system to select"
      dropdownStyle={{ minWidth: "500px" }}
      data-testid="system-select"
      {...props}
      showSearch
      filterOption={false}
      options={options}
      onSearch={onSearch}
      loading={props.loading || isFetching}
    />
  );
};
