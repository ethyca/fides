import { AntSelect as Select, AntSelectProps as SelectProps } from "fidesui";
import {
  MouseEventHandler,
  ReactNode,
  useCallback,
  useMemo,
  useState,
} from "react";

import { useGetSystemsQuery } from "~/features/system/system.slice";

import { CustomSelectOption } from "../form/CustomSelectOption";
import { debounce } from "../utils";

const OPTIONS_LIMIT = 25;

const dropdownRender = (
  menu: ReactNode,
  onAddSystem: MouseEventHandler<HTMLElement>,
) => {
  return (
    <>
      <CustomSelectOption
        onClick={onAddSystem}
        data-testid="add-new-system"
        id="add-new-system"
      >
        Add new system +
      </CustomSelectOption>
      {menu}
    </>
  );
};

interface SystemSelectProps
  extends Omit<SelectProps, "options" | "filterOption" | "onSearch"> {
  onAddSystem?: MouseEventHandler<HTMLButtonElement>;
}

export const SystemSelect = ({ onAddSystem, ...props }: SystemSelectProps) => {
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
      dropdownRender={
        onAddSystem ? (menu) => dropdownRender(menu, onAddSystem) : undefined
      }
      data-testid="system-select"
      {...props}
      filterOption={false}
      options={options}
      onSearch={onSearch}
      loading={props.loading || isFetching}
    />
  );
};
