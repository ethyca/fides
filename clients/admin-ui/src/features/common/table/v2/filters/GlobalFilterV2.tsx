import { debounce } from "common/utils";
import { Box } from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import SearchInput from "~/features/common/SearchInput";

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

  const onClear = useCallback(() => {
    setValue(undefined);
    setGlobalFilter(undefined);
  }, [setValue, setGlobalFilter]);

  // Keep local state in sync with the externally-managed `globalFilter`.
  useEffect(() => {
    if (!globalFilter) {
      setValue(undefined);
    }
  }, [globalFilter]);

  return (
    <Box maxWidth="424px" width="100%">
      <SearchInput
        onChange={(changeValue) => {
          setValue(changeValue);
          onChange(changeValue);
        }}
        onClear={onClear}
        value={value || ""}
        placeholder={placeholder}
        data-testid={testid}
      />
    </Box>
  );
};
