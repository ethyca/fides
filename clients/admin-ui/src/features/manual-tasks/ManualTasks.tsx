import { useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";

import { ManualTasksTable } from "./components/ManualTasksTable";

export const ManualTasks = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  return (
    <div className="mt-2 space-y-4">
      <DebouncedSearchInput
        placeholder="Search by name or description..."
        value={searchTerm}
        onChange={handleSearchChange}
        className="max-w-sm"
      />

      <ManualTasksTable searchTerm={searchTerm} />
    </div>
  );
};
