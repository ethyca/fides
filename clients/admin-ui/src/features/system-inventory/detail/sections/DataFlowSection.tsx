import {
  sankey,
  sankeyJustify,
  type SankeyLink,
  sankeyLinkHorizontal,
  type SankeyNode,
} from "d3-sankey";
import { Button, Flex, Text, Typography } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo, useState } from "react";

import type { MockSystem } from "../../types";
import RelationshipPickerModal from "../modals/RelationshipPickerModal";

const { Title } = Typography;

interface DataFlowSectionProps {
  system: MockSystem;
}

type FlowLayer = "producer" | "self" | "consumer";

interface SankeyNodeData {
  id: string;
  label: string;
  layer: FlowLayer;
}

interface SankeyLinkData {
  source: string;
  target: string;
  value: number;
}

type LaidOutNode = SankeyNode<SankeyNodeData, SankeyLinkData>;
type LaidOutLink = SankeyLink<SankeyNodeData, SankeyLinkData>;

const LAYER_COLORS: Record<FlowLayer, string> = {
  producer: palette.FIDESUI_OLIVE,
  self: palette.FIDESUI_MINOS,
  consumer: palette.FIDESUI_TERRACOTTA,
};

const WIDTH = 960;
const HEIGHT = 440;

const linkPathGenerator = sankeyLinkHorizontal<
  SankeyNodeData,
  SankeyLinkData
>();

const buildGraph = (system: MockSystem) => {
  const selfId = `self:${system.fides_key}`;
  const nodes: SankeyNodeData[] = [
    { id: selfId, label: system.name, layer: "self" },
  ];
  const links: SankeyLinkData[] = [];

  // Producers = systems this system consumes FROM (upstream)
  const producers = system.relationships.filter((r) => r.role === "consumer");
  // Consumers = systems this system produces FOR (downstream)
  const consumers = system.relationships.filter((r) => r.role === "producer");

  producers.forEach((rel) => {
    const nodeId = `producer:${rel.systemKey}`;
    nodes.push({ id: nodeId, label: rel.systemName, layer: "producer" });
    links.push({ source: nodeId, target: selfId, value: 1 });
  });

  consumers.forEach((rel) => {
    const nodeId = `consumer:${rel.systemKey}`;
    nodes.push({ id: nodeId, label: rel.systemName, layer: "consumer" });
    links.push({ source: selfId, target: nodeId, value: 1 });
  });

  return {
    nodes,
    links,
    producerCount: producers.length,
    consumerCount: consumers.length,
  };
};

const DataFlowSection = ({ system }: DataFlowSectionProps) => {
  const [pickerRole, setPickerRole] = useState<"producer" | "consumer" | null>(
    null,
  );

  const { nodes, links, producerCount, consumerCount } = useMemo(
    () => buildGraph(system),
    [system],
  );

  const layerById = useMemo(() => {
    const map = new Map<string, FlowLayer>();
    nodes.forEach((node) => map.set(node.id, node.layer));
    return map;
  }, [nodes]);

  const layout = useMemo(() => {
    if (links.length === 0) {
      return null;
    }
    const generator = sankey<SankeyNodeData, SankeyLinkData>()
      .nodeId((node) => node.id)
      .nodeAlign(sankeyJustify)
      .nodeWidth(14)
      .nodePadding(16)
      .extent([
        [24, 24],
        [WIDTH - 24, HEIGHT - 24],
      ]);
    return generator({
      nodes: nodes.map((n) => ({ ...n })),
      links: links.map((l) => ({ ...l })),
    });
  }, [nodes, links]);

  const existingKeys = new Set(system.relationships.map((r) => r.systemKey));

  const hasFlow = producerCount > 0 || consumerCount > 0;
  const laidOutNodes = (layout?.nodes ?? []) as LaidOutNode[];
  const laidOutLinks = (layout?.links ?? []) as LaidOutLink[];

  return (
    <Flex vertical gap={12} className="min-w-0">
      <Flex justify="space-between" align="center">
        <Title level={4} className="!m-0">
          System data flow
        </Title>
        <Flex gap="small">
          <Button size="small" onClick={() => setPickerRole("producer")}>
            + Add producer
          </Button>
          <Button size="small" onClick={() => setPickerRole("consumer")}>
            + Add consumer
          </Button>
        </Flex>
      </Flex>
      <Text type="secondary" className="text-sm">
        Systems that produce data into {system.name} (upstream) and systems that
        consume data from it (downstream).
      </Text>

      {/* Legend */}
      <Flex gap={20} align="center">
        <Flex align="center" gap={6}>
          <div
            className="size-2 rounded-full"
            style={{ backgroundColor: LAYER_COLORS.producer }}
          />
          <Text className="text-[10px]">Producers ({producerCount})</Text>
        </Flex>
        <Flex align="center" gap={6}>
          <div
            className="size-2 rounded-full"
            style={{ backgroundColor: LAYER_COLORS.self }}
          />
          <Text className="text-[10px]">{system.name}</Text>
        </Flex>
        <Flex align="center" gap={6}>
          <div
            className="size-2 rounded-full"
            style={{ backgroundColor: LAYER_COLORS.consumer }}
          />
          <Text className="text-[10px]">Consumers ({consumerCount})</Text>
        </Flex>
      </Flex>

      {hasFlow ? (
        <svg
          role="img"
          aria-label={`System data flow for ${system.name}`}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          preserveAspectRatio="xMidYMid meet"
          className="w-full"
          style={{ maxHeight: HEIGHT }}
        >
          <g>
            {laidOutLinks.map((link) => {
              const sourceNode = link.source as LaidOutNode;
              const targetNode = link.target as LaidOutNode;
              const sourceLayer = layerById.get(sourceNode.id) ?? "self";
              const color =
                sourceLayer === "self"
                  ? palette.FIDESUI_NEUTRAL_300
                  : LAYER_COLORS[sourceLayer];
              const pathD = linkPathGenerator(link);
              if (!pathD) {
                return null;
              }
              return (
                <path
                  key={`${sourceNode.id}->${targetNode.id}`}
                  d={pathD}
                  fill="none"
                  stroke={color}
                  strokeOpacity={0.3}
                  strokeWidth={Math.max(3, link.width ?? 0)}
                />
              );
            })}
          </g>
          <g>
            {laidOutNodes.map((node) => {
              const x0 = node.x0 ?? 0;
              const x1 = node.x1 ?? 0;
              const y0 = node.y0 ?? 0;
              const y1 = node.y1 ?? 0;
              const layer = layerById.get(node.id) ?? "self";
              const isRight = layer === "consumer";
              const isSelf = layer === "self";
              return (
                <g key={node.id}>
                  <rect
                    x={x0}
                    y={y0}
                    width={x1 - x0}
                    height={Math.max(4, y1 - y0)}
                    fill={LAYER_COLORS[layer]}
                    rx={3}
                  />
                  <text
                    x={isRight ? x0 - 8 : x1 + 8}
                    y={(y0 + y1) / 2}
                    dy="0.35em"
                    textAnchor={isRight ? "end" : "start"}
                    fontSize={isSelf ? 13 : 11}
                    fontWeight={isSelf ? 600 : 400}
                    fill={palette.FIDESUI_NEUTRAL_900}
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      ) : (
        <Flex
          justify="center"
          align="center"
          className="rounded-lg py-12"
          style={{ backgroundColor: palette.FIDESUI_BG_DEFAULT }}
        >
          <Flex vertical align="center" gap={8}>
            <Text type="secondary" className="text-sm">
              No data flow connections yet
            </Text>
            <Text type="secondary" className="text-xs">
              Add producers or consumers to visualize how data flows through{" "}
              {system.name}.
            </Text>
          </Flex>
        </Flex>
      )}

      <RelationshipPickerModal
        open={pickerRole !== null}
        onClose={() => setPickerRole(null)}
        role={pickerRole ?? "producer"}
        systemFidesKey={system.fides_key}
        existingKeys={existingKeys}
      />
    </Flex>
  );
};

export default DataFlowSection;
