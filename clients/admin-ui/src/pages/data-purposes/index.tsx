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
  const {
    items: purposes,
    filterOptions,
    isLoading,
    error,
    searchQuery,
    setSearchQuery,
    dataUseFilter,
    setDataUseFilter,
    consumerFilter,
    setConsumerFilter,
    categoryFilter,
    setCategoryFilter,
    statusFilter,
    setStatusFilter,
    filterParams,
  } = usePurposesList();
  const isError = Boolean(error);
  const { data: summaries = [] } = useGetPurposeSummariesQuery();
  const { downloadRoPA, isDownloadingRoPA } = useDownloadRoPA();

  return (
    <FixedLayout title="Purposes" fullHeight>
      <PageHeader
        heading="Purposes"
        rightContent={
          <Flex gap="small">
            <Button
              icon={<Icons.Download />}
              onClick={() => downloadRoPA(filterParams)}
              loading={isDownloadingRoPA}
              disabled={purposes.length === 0}
            >
              Download RoPA
            </Button>
            <Button
              type="primary"
              icon={<Icons.Add />}
              onClick={() => setModalOpen(true)}
            >
              New purpose
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
          onSearchChange={setSearchQuery}
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
