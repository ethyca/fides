import "@xyflow/react/dist/style.css";

import {
    Background,
    BackgroundVariant,
    Controls,
    Edge,
    MarkerType,
    MiniMap,
    Node,
    NodeTypes,
    ReactFlow,
    ReactFlowProvider,
    useReactFlow,
} from "@xyflow/react";
import { Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import React, { useCallback, useContext, useEffect, useMemo } from "react";

import { DatamapGraphContext } from "~/features/datamap/datamap-graph/DatamapGraphContext";
import DatamapSystemNode from "~/features/datamap/DatamapSystemNode";
import { getLayoutedElements } from "~/features/datamap/layout-utils";
import { SpatialData } from "~/features/datamap/types";

type UseDatamapGraphProps = {
    data: SpatialData;
};

const useDatamapGraph = ({ data }: UseDatamapGraphProps) => {
    // Transform nodes from the datamap format to ReactFlow format
    const initialNodes: Node[] = useMemo(
        () =>
            data.nodes.map((node) => ({
                id: node.id,
                data: {
                    label: node.name,
                    description: node.description,
                },
                position: { x: 0, y: 0 }, // Initial positions will be set by the layout
                type: "systemNode", // Use our custom node type
            })),
        [data.nodes],
    );

    // Transform links from the datamap format to ReactFlow edges
    const initialEdges: Edge[] = useMemo(
        () =>
            data.links.map((link, index) => ({
                id: `edge-${index}`,
                source: link.source,
                target: link.target,
                markerEnd: {
                    type: MarkerType.ArrowClosed,
                    color: palette.FIDESUI_NEUTRAL_300,
                    width: 15,
                    height: 15,
                },
                style: {
                    stroke: palette.FIDESUI_NEUTRAL_300,
                    strokeWidth: 1.5,
                    strokeOpacity: 0.8,
                },
                animated: false,
            })),
        [data.links],
    );

    // Apply layout to position nodes
    const { nodes, edges } = useMemo(
        () => getLayoutedElements(initialNodes, initialEdges, "LR"),
        [initialNodes, initialEdges],
    );

    return {
        nodes,
        edges,
    };
};

interface DatamapGraphProps {
    data: SpatialData;
    setSelectedSystemId: (id: string) => void;
}

const DatamapGraph = ({ data, setSelectedSystemId }: DatamapGraphProps) => {
    const { nodes, edges } = useDatamapGraph({ data });
    const reactFlowInstance = useReactFlow();
    const datamapGraphRef = useContext(DatamapGraphContext);

    // Define the custom node types
    const nodeTypes = useMemo<NodeTypes>(
        () => ({
            systemNode: DatamapSystemNode,
        }),
        [],
    );

    // Store the ReactFlow instance in the context
    useEffect(() => {
        datamapGraphRef.current = reactFlowInstance;

        // Cleanup function
        return () => {
            datamapGraphRef.current = undefined;
        };
    }, [reactFlowInstance, datamapGraphRef]);

    // Center the graph and adjust view on initial load
    useEffect(() => {
        if (nodes.length > 0) {
            setTimeout(() => {
                reactFlowInstance.fitView({ padding: 0.2 });
            }, 150);
        }
    }, [nodes, reactFlowInstance]);

    // Handle node selection
    const onNodeClick = useCallback(
        (_: React.MouseEvent, node: Node) => {
            setSelectedSystemId(node.id);
        },
        [setSelectedSystemId],
    );

    return (
        <Box boxSize="100%" data-testid="reactflow-graph" position="absolute">
            <Box boxSize="100%" bgColor={palette.FIDESUI_BG_CORINTH}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodeClick={onNodeClick}
                    nodeTypes={nodeTypes}
                    nodesFocusable={false}
                    edgesFocusable={false}
                    connectOnClick={false}
                    nodesConnectable={false}
                    elementsSelectable
                    fitView
                    minZoom={0.3}
                    maxZoom={2}
                    proOptions={{ hideAttribution: true }}
                >
                    <Background
                        color={palette.FIDESUI_NEUTRAL_100}
                        variant={BackgroundVariant.Dots}
                        size={3}
                    />
                    <MiniMap nodeStrokeWidth={3} pannable />
                    <Controls showInteractive={false} />
                </ReactFlow>
            </Box>
        </Box>
    );
};

const DatamapGraphWithProvider = (props: DatamapGraphProps) => {
    return (
        <ReactFlowProvider>
            <DatamapGraph {...props} />
        </ReactFlowProvider>
    );
};

export default DatamapGraphWithProvider;
