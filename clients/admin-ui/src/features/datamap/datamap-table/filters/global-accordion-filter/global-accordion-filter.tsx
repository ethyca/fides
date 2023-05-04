import { Box } from "@fidesui/react";
import { useState } from "react";
import { useAsyncDebounce } from "react-table";

import SearchBar from "~/features/common/SearchBar";

type GlobalFilterProps = {
  globalFilter: any;
  setGlobalFilter: (filterValue: any) => void;
  placeholder?: string;
};

const GlobalFilter = ({
  globalFilter,
  setGlobalFilter,
  placeholder,
}: GlobalFilterProps) => {
  const [value, setValue] = useState(globalFilter);

  const onChange = useAsyncDebounce((searchValue) => {
    setGlobalFilter(searchValue || undefined);
  }, 200);

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

export default GlobalFilter;
