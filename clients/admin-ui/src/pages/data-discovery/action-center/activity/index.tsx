import { NextPage } from "next";

import { useSearch } from "~/features/common/hooks/useSearch";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { InProgressMonitorTasksList } from "~/features/data-discovery-and-detection/action-center/components/InProgressMonitorTasksList";

import { ROOT_ACTION_CENTER_CONFIG } from "..";

const ActionCenterActivityPage: NextPage = () => {
  const { searchQuery, updateSearch } = useSearch();

  return (
    <ActionCenterLayout
      routeConfig={ROOT_ACTION_CENTER_CONFIG}
      searchProps={{
        value: searchQuery ?? "",
        onSearch: updateSearch,
        placeholder: "Search by monitor name...",
      }}
    >
      <InProgressMonitorTasksList
        searchQuery={searchQuery}
        onSearchChange={updateSearch}
      />
    </ActionCenterLayout>
  );
};

export default ActionCenterActivityPage;
