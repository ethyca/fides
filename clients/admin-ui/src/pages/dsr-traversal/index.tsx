import { NextPage } from "next";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { TraversalVisualizerPage } from "~/features/dsr-traversal-visualizer/TraversalVisualizerPage";
import { ActionType } from "~/features/dsr-traversal-visualizer/types";

const DsrTraversalIndex: NextPage = () => (
  <FixedLayout title="DSR Traversal" fullHeight>
    <PageHeader heading="Request workflows" isSticky={false} />
    <TraversalVisualizerPage
      propertyKey={null}
      actionType={ActionType.ACCESS}
    />
  </FixedLayout>
);

export default DsrTraversalIndex;
