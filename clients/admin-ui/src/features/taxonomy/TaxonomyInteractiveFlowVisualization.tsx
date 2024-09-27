import "@xyflow/react/dist/style.css";

import { Background, BackgroundVariant, ReactFlow } from "@xyflow/react";

import { TaxonomyEntity } from "./types";

interface TaxonomyInteractiveFlowVisualizationProps {
  taxonomyItems: TaxonomyEntity[];
}

const TaxonomyInteractiveFlowVisualization = ({
  taxonomyItems,
}: TaxonomyInteractiveFlowVisualizationProps) => {
  const initialNodes = [
    { id: "1", position: { x: 0, y: 0 }, data: { label: "something" } },
    { id: "2", position: { x: 0, y: 100 }, data: { label: "something else" } },
  ];

  const initialEdges = [{ id: "e1-2", source: "1", target: "2" }];

  console.log("taxonomyItems", taxonomyItems);

  return (
    <div className="h-[400px] w-full">
      <ReactFlow nodes={initialNodes} edges={initialEdges}>
        <Background color="#ccc" variant={BackgroundVariant.Dots} />
      </ReactFlow>
    </div>
  );
};
export default TaxonomyInteractiveFlowVisualization;
