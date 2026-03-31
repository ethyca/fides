import { Button } from "fidesui";
import { NextPage } from "next";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import NewPurposeModal from "~/features/data-purposes/NewPurposeModal";
import PurposeCardGrid from "~/features/data-purposes/PurposeCardGrid";

const DataPurposesPage: NextPage = () => {
  const [modalOpen, setModalOpen] = useState(false);

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
      <PurposeCardGrid />
      <NewPurposeModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => setModalOpen(false)}
      />
    </FixedLayout>
  );
};

export default DataPurposesPage;
