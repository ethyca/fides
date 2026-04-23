import { Button, Flex, Icons, Result, Spin } from "fidesui";
import { NextPage } from "next";
import { useCallback, useState } from "react";

import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { useGetPurposeSummariesQuery } from "~/features/data-purposes/data-purpose.slice";
import NewPurposeModal from "~/features/data-purposes/NewPurposeModal";
import PurposeCardGrid from "~/features/data-purposes/PurposeCardGrid";
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

  const handleDownloadRoPA = useCallback(() => {
    const summariesByKey = new Map(summaries.map((s) => [s.fides_key, s]));
    const header = [
      "Reference",
      "Processing activity",
      "Description",
      "Purpose of processing",
      "Lawful basis (Art. 6)",
      "Special category basis (Art. 9)",
      "Categories of data subjects",
      "Categories of personal data",
      "Categories of personal data (detected)",
      "Retention period (days)",
      "Features",
      "Last reviewed",
    ];
    const rows = purposes.map((p) => [
      p.fides_key,
      p.name,
      p.description ?? "",
      p.data_use,
      p.legal_basis_for_processing ?? "",
      p.special_category_legal_basis ?? "",
      p.data_subject ?? "",
      (p.data_categories ?? []).join("; "),
      (summariesByKey.get(p.fides_key)?.detected_data_categories ?? []).join(
        "; ",
      ),
      p.retention_period ?? "",
      (p.features ?? []).join("; "),
      p.updated_at ?? "",
    ]);
    // Prefix BOM and use CRLF so Excel on Windows reads UTF-8 and line breaks
    // correctly; RFC 4180 requires CRLF.
    const csvBody = [header, ...rows]
      .map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","))
      .join("\r\n");
    const csv = `\ufeff${csvBody}`;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ropa.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, [purposes, summaries]);

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
              onClick={handleDownloadRoPA}
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
