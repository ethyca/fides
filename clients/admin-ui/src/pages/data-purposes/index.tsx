import { Button, Flex, Icons, Result, Spin } from "fidesui";
import { NextPage } from "next";
import { useState } from "react";

import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { useGetPurposeSummariesQuery } from "~/features/data-purposes/data-purpose.slice";
import NewPurposeModal from "~/features/data-purposes/NewPurposeModal";
import PurposeCardGrid from "~/features/data-purposes/PurposeCardGrid";
import { downloadRoPA } from "~/features/data-purposes/ropaExport";
import usePurposesList from "~/features/data-purposes/usePurposesList";

const DataPurposesPage: NextPage = () => {
  const { flags } = useFeatures();
  const [modalOpen, setModalOpen] = useState(false);
  const [dataUseFilter, setDataUseFilter] = useState<string | null>(null);
  const {
    items: purposes,
    searchQuery,
    updateSearch,
    isLoading,
    error,
  } = usePurposesList({
    enabled: flags.alphaPurposeBasedAccessControl,
    dataUseFilter,
  });
  const isError = Boolean(error);
  const { data: summaries = [] } = useGetPurposeSummariesQuery(undefined, {
    skip: !flags.alphaPurposeBasedAccessControl,
  });

  if (!flags.alphaPurposeBasedAccessControl) {
    return (
      <FixedLayout title="Purposes" fullHeight>
        <Result
          status="error"
          title="Purpose management is not enabled"
          subTitle="Turn on the alpha purpose-based access control flag to preview this feature."
        />
      </FixedLayout>
    );
  }

  let body: React.ReactNode;
  if (isLoading) {
    body = (
      <Flex justify="center" className="mt-12">
        <Spin size="large" />
      </Flex>
    );
  } else if (isError) {
    body = (
      <Result
        status="error"
        title="Couldn't load purposes"
        subTitle="Something went wrong fetching purposes. Refresh to try again."
      />
    );
  } else {
    body = (
      <PurposeCardGrid
        purposes={purposes}
        summaries={summaries}
        dataUseFilter={dataUseFilter}
        onDataUseFilterChange={setDataUseFilter}
        searchQuery={searchQuery}
        onSearchChange={updateSearch}
        onCreatePurpose={() => setModalOpen(true)}
      />
    );
  }

  return (
    <FixedLayout title="Purposes" fullHeight>
      <PageHeader
        heading="Purposes"
        rightContent={
          <Flex gap="small">
            <Button
              icon={<Icons.Download />}
              onClick={() => downloadRoPA(purposes, summaries)}
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
      {body}
      <NewPurposeModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => setModalOpen(false)}
      />
    </FixedLayout>
  );
};

export default DataPurposesPage;
