import { useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";

import { ManualTasksTable } from "./components/ManualTasksTable";

export const ManualTasks = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  return (
    <div className="p-4">
      <div className="mb-4">
        <DebouncedSearchInput
          placeholder="Search by name or description..."
          value={searchTerm}
          onChange={handleSearchChange}
          className="max-w-sm"
        />
      </div>

      <ManualTasksTable searchTerm={searchTerm} />
    </div>
  );
};
