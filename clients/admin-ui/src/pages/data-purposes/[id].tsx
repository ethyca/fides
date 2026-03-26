import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import PurposeDetail from "~/features/data-purposes/PurposeDetail";
import { usePurposes } from "~/features/data-purposes/usePurposes";

const PurposeDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const { getPurpose, getCoverage, getAssignments, getDatasetAssignments } =
    usePurposes();

  const purpose = id ? getPurpose(id as string) : null;
  const coverage = id ? getCoverage(id as string) : null;
  const systems = id ? getAssignments(id as string) : [];
  const datasets = id ? getDatasetAssignments(id as string) : [];

  if (!purpose || !coverage) {
    return null;
  }

  return (
    <FixedLayout title="Data purposes">
      <PageHeader
        heading="Data purposes"
        breadcrumbItems={[
          { title: "All purposes", href: DATA_PURPOSES_ROUTE },
          { title: purpose.name },
        ]}
      />
      <PurposeDetail
        purpose={purpose}
        coverage={coverage}
        systems={systems}
        datasets={datasets}
      />
    </FixedLayout>
  );
};

export default PurposeDetailPage;
