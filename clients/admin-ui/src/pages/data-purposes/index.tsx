import { Button, Flex, Icons } from "fidesui";
import { NextPage } from "next";
import { useCallback, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import NewPurposeModal from "~/features/data-purposes/NewPurposeModal";
import PurposeCardGrid from "~/features/data-purposes/PurposeCardGrid";
import { MOCK_PURPOSES } from "~/features/data-purposes/mockData";
import { usePurposes } from "~/features/data-purposes/usePurposes";

const DataPurposesPage: NextPage = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const { purposes, getSummaries, createPurpose } = usePurposes();

  const handleDownloadRoPA = useCallback(() => {
    const header = [
      "Name",
      "Data use",
      "Data subjects",
      "Legal basis",
      "Retention (days)",
      "Data categories",
      "Updated",
    ];
    const rows = MOCK_PURPOSES.map((p) => [
      p.name,
      p.data_use,
      p.data_subjects.join("; "),
      p.legal_basis,
      p.retention_period_days ?? "",
      p.data_categories.join("; "),
      p.updated_at,
    ]);
    const csv = [header, ...rows]
      .map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ropa.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  return (
    <FixedLayout title="Purposes">
      <PageHeader
        heading="Purposes"
        rightContent={
          <Flex gap="small">
            <Button icon={<Icons.Download />} onClick={handleDownloadRoPA}>
              Download RoPA
            </Button>
            <Button type="primary" onClick={() => setModalOpen(true)}>
              + New purpose
            </Button>
          </Flex>
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
