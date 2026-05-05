import { Button, Flex, Icons, Result, Spin } from "fidesui";
import { NextPage } from "next";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import NewPurposeModal from "~/features/data-purposes/NewPurposeModal";
import PurposeCardGrid from "~/features/data-purposes/PurposeCardGrid";
import useDownloadRoPA from "~/features/data-purposes/useDownloadRoPA";
import usePurposesList from "~/features/data-purposes/usePurposesList";

const DataPurposesPage: NextPage = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const { items: purposes, isLoading, error, filterParams } = usePurposesList();
  const isError = Boolean(error);
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
        <PurposeCardGrid onCreatePurpose={() => setModalOpen(true)} />
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
