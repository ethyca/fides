import { Button } from "fidesui";
import { NextPage } from "next";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import NewPurposeModal from "~/features/data-purposes/NewPurposeModal";
import PurposeCardGrid from "~/features/data-purposes/PurposeCardGrid";
import { usePurposes } from "~/features/data-purposes/usePurposes";

const DataPurposesPage: NextPage = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const { purposes, getSummaries, createPurpose } = usePurposes();

  return (
    <FixedLayout title="Data purposes">
      <PageHeader
        heading="Data purposes"
        rightContent={
          <Button type="primary" onClick={() => setModalOpen(true)}>
            + New purpose
          </Button>
        }
      />
      <PurposeCardGrid purposes={purposes} summaries={getSummaries} />
      <NewPurposeModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => setModalOpen(false)}
        createPurpose={createPurpose}
      />
    </FixedLayout>
  );
};

export default DataPurposesPage;
