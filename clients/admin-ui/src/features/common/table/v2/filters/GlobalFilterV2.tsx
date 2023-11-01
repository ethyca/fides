import { Box } from "@fidesui/react";
import SearchBar from "common/SearchBar";
import { debounce } from "common/utils";
import { useMemo, useState } from "react";

type GlobalFilterProps = {
  globalFilter: any;
  setGlobalFilter: (filterValue: any) => void;
  placeholder?: string;
};

export const GlobalFilterV2 = ({
  globalFilter,
  setGlobalFilter,
  placeholder,
}: GlobalFilterProps) => {
  const [value, setValue] = useState(globalFilter);

  const onChange = useMemo(
    () => debounce(setGlobalFilter, 200),
    [setGlobalFilter]
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
      />
    </Box>
  );
};
