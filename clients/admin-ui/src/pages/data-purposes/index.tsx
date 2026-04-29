import { Button, Flex, Icons, Result, Spin } from "fidesui";
import { NextPage } from "next";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { useGetPurposeSummariesQuery } from "~/features/data-purposes/data-purpose.slice";
import NewPurposeModal from "~/features/data-purposes/NewPurposeModal";
import PurposeCardGrid from "~/features/data-purposes/PurposeCardGrid";
import useDownloadRoPA from "~/features/data-purposes/useDownloadRoPA";
import usePurposesList from "~/features/data-purposes/usePurposesList";

const DataPurposesPage: NextPage = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [dataUseFilter, setDataUseFilter] = useState<string | null>(null);
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const {
    items: purposes,
    filterOptions,
    searchQuery,
    updateSearch,
    isLoading,
    error,
  } = usePurposesList({
    dataUseFilter,
    consumerFilter,
    categoryFilter,
    statusFilter,
  });
  const isError = Boolean(error);
  const { data: summaries = [] } = useGetPurposeSummariesQuery();
  const { downloadRoPA, isDownloadingRoPA } = useDownloadRoPA();

  const clearFilters = () => {
    setDataUseFilter(null);
    setConsumerFilter(null);
    setCategoryFilter(null);
    setStatusFilter(null);
    updateSearch("");
  };

  return (
    <FixedLayout title="Purposes" fullHeight>
      <PageHeader
        heading="Purposes"
        rightContent={
          <Flex gap="small">
            <Button
              icon={<Icons.Download />}
              onClick={() =>
                downloadRoPA({
                  search: searchQuery || undefined,
                  data_use: dataUseFilter ?? undefined,
                  consumer: consumerFilter ?? undefined,
                  category: categoryFilter ?? undefined,
                  status: statusFilter ?? undefined,
                })
              }
              loading={isDownloadingRoPA}
              disabled={purposes.length === 0}
            >
              Download RoPA
            </Button>
            <Button type="primary" onClick={() => setModalOpen(true)}>
              + New purpose
            </Button>
          </Flex>
        }
      />
      {isLoading && (
        <Flex justify="center" className="mt-12">
          <Spin size="large" />
        </Flex>
      )}
      {!isLoading && isError && (
        <Result
          status="error"
          title="Couldn't load purposes"
          subTitle="Something went wrong fetching purposes. Refresh to try again."
        />
      )}
      {!isLoading && !isError && (
        <PurposeCardGrid
          purposes={purposes}
          summaries={summaries}
          filterOptions={filterOptions}
          dataUseFilter={dataUseFilter}
          onDataUseFilterChange={setDataUseFilter}
          consumerFilter={consumerFilter}
          onConsumerFilterChange={setConsumerFilter}
          categoryFilter={categoryFilter}
          onCategoryFilterChange={setCategoryFilter}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          searchQuery={searchQuery}
          onSearchChange={updateSearch}
          onClearFilters={clearFilters}
          onCreatePurpose={() => setModalOpen(true)}
        />
      )}
      <NewPurposeModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => setModalOpen(false)}
      />
    </FixedLayout>
  );
};

export default DataPurposesPage;
