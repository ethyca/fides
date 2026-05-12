import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { TraversalVisualizerPage } from "~/features/dsr-traversal-visualizer/TraversalVisualizerPage";
import { ActionType } from "~/features/dsr-traversal-visualizer/types";

const DsrTraversalPropertyPage: NextPage = () => {
  const router = useRouter();
  const propertyKey =
    typeof router.query.propertyKey === "string"
      ? router.query.propertyKey
      : null;
  const actionTypeParam = router.query.actionType;
  const actionType =
    Array.isArray(actionTypeParam) && actionTypeParam[0] === ActionType.ERASURE
      ? ActionType.ERASURE
      : ActionType.ACCESS;
  return (
    <FixedLayout title="DSR Traversal" fullHeight>
      <PageHeader heading="Request workflows" isSticky={false} />
      <TraversalVisualizerPage
        propertyKey={propertyKey}
        actionType={actionType}
      />
    </FixedLayout>
  );
};

export default DsrTraversalPropertyPage;
