import { Box } from "@fidesui/react";
import { useState } from "react";

import SearchBar from "~/features/common/SearchBar";

const SystemCatalog = () => {
  const [searchFilter, setSearchFilter] = useState("");

  return (
    <Box>
      <Box maxWidth="30vw">
        <SearchBar
          search={searchFilter}
          onChange={setSearchFilter}
          placeholder="Search for a system"
          data-testid="system-catalog-search"
          withClear
        />
      </Box>
    </Box>
  );
};

export default SystemCatalog;
