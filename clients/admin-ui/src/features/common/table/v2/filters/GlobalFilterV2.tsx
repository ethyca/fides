import SearchBar from "common/SearchBar";
import { debounce } from "common/utils";
import { Box } from "fidesui";
import { useMemo, useState } from "react";

type GlobalFilterProps = {
  globalFilter: any;
  setGlobalFilter: (filterValue: any) => void;
  placeholder?: string;
  testid?: string;
};

export const GlobalFilterV2 = ({
  globalFilter,
  setGlobalFilter,
  placeholder,
  testid = "global-text-filter",
}: GlobalFilterProps) => {
  const [value, setValue] = useState(globalFilter);

  const onChange = useMemo(
    () => debounce(setGlobalFilter, 200),
    [setGlobalFilter],
  );

  const onClear = () => {
    setValue(undefined);
    setGlobalFilter(undefined);
  };

  return (
    <Box maxWidth="510px" width="100%">
      <SearchBar
        onChange={(changeValue) => {
          setValue(changeValue);
          onChange(changeValue);
        }}
        onClear={onClear}
        search={value || ""}
        placeholder={placeholder}
        data-testid={testid}
      />
    </Box>
  );
};
