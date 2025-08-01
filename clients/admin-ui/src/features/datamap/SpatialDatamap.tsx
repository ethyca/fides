import { Row } from "@tanstack/react-table";
import { Box } from "fidesui";
import React, { useContext, useMemo } from "react";

import DatamapGraph from "~/features/datamap/DatamapGraph";

import { DatamapRow } from "./datamap.slice";
import DatamapTableContext from "./datamap-table/DatamapTableContext";
import { Link, SystemNode } from "./types";

const useSpatialDatamap = (rows: Row<DatamapRow>[]) => {
  const systemKeysFromFilteredRows = useMemo(
    () => new Set(rows?.map((row) => row.original["system.fides_key"])),
    [rows],
  );
  const datamapBySystem = useMemo(
    () =>
      rows.reduce(
        (draft, obj) => {
          const key = obj.original["system.fides_key"];
          if (!draft[key]) {
            draft[key] = {
              name: obj.original["system.name"],
              description: obj.original["system.description"],
              ingress: obj.original["system.ingress"]
                ? obj.original["system.ingress"].split(", ")
                : [],
              egress: obj.original["system.egress"]
                ? obj.original["system.egress"].split(", ")
                : [],
              id: obj.original["system.fides_key"],
            };
          }
          return draft;
        },
        {} as Record<string, SystemNode>,
      ),
    [rows],
  );
  const data = useMemo(() => {
    let nodes: SystemNode[] = [];
    const links: Set<string> = new Set([]);
    if (datamapBySystem) {
      nodes = Object.values(datamapBySystem);
      nodes
        .map<Link[]>((system) => [
          ...system.ingress
            .filter((ingress_system) => datamapBySystem[ingress_system])
            .map((ingress_system) => ({
              source: ingress_system,
              target: system.id,
            })),
          ...system.egress
            .filter((egress_system) => datamapBySystem[egress_system])
            .map((egress_system) => ({
              source: system.id,
              target: egress_system,
            })),
        ])
        .flatMap((link) => link)
        .forEach((link) => links.add(JSON.stringify(link)));
    }

    return {
      nodes,
      links: Array.from(links).map((l) => JSON.parse(l)) as Link[],
    };
  }, [datamapBySystem]);

  return {
    data,
    highlightedNodes: systemKeysFromFilteredRows,
  };
};

/**
 * Props for the SpatialDatamap component
 */
type SpatialDatamapProps = {
  /** Function to call when a system node is selected in the graph */
  setSelectedSystemId: (id: string) => void;
  /** Currently selected system ID to highlight in the graph */
  selectedSystemId?: string;
};

const SpatialDatamap = ({
  setSelectedSystemId,
  selectedSystemId,
}: SpatialDatamapProps) => {
  const { tableInstance } = useContext(DatamapTableContext);

  if (!tableInstance) {
    return null;
  }
  const { rows } = tableInstance.getRowModel();

  const {
    data,
    // eslint-disable-next-line react-hooks/rules-of-hooks
  } = useSpatialDatamap(rows);

  return (
    <Box boxSize="100%" minHeight="600px" position="relative">
      <DatamapGraph
        data={data}
        setSelectedSystemId={setSelectedSystemId}
        selectedSystemId={selectedSystemId}
      />
    </Box>
  );
};

export default SpatialDatamap;
