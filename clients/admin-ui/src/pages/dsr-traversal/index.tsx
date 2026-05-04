import { NextPage } from "next";

import FixedLayout from "~/features/common/FixedLayout";
import TraversalVisualizerPage from "~/features/dsr-traversal-visualizer/TraversalVisualizerPage";

const DsrTraversalIndex: NextPage = () => (
  <FixedLayout title="DSR Traversal" fullHeight>
    <TraversalVisualizerPage propertyKey={null} actionType="access" />
  </FixedLayout>
);

export default DsrTraversalIndex;
