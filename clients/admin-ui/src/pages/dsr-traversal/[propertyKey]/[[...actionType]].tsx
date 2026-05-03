import { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import TraversalVisualizerPage from "~/features/dsr-traversal-visualizer/TraversalVisualizerPage";

const DsrTraversalPropertyPage: NextPage = () => {
  const router = useRouter();
  const propertyKey =
    typeof router.query.propertyKey === "string"
      ? router.query.propertyKey
      : null;
  const actionTypeParam = router.query.actionType;
  const actionType =
    Array.isArray(actionTypeParam) && actionTypeParam[0] === "erasure"
      ? "erasure"
      : "access";
  return (
    <FixedLayout title="DSR Traversal" fullHeight>
      <TraversalVisualizerPage
        propertyKey={propertyKey}
        actionType={actionType}
      />
    </FixedLayout>
  );
};

export default DsrTraversalPropertyPage;
