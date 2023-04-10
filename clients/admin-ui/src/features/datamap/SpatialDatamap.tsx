import { Box } from "@fidesui/react";
import React, { useContext, useMemo } from "react";
import { Row } from "react-table";

import CytoscapeGraph from "~/features/datamap/CytoscapeGraph";

import { DatamapRow } from "./datamap.slice";
import DatamapTableContext from "./datamap-table/DatamapTableContext";
import { Link, SetSelectedSystemId, SystemNode } from "./types";

const useSpatialDatamap = (rows: Row<DatamapRow>[]) => {
  const systemKeysFromFilteredRows = useMemo(
    () => new Set(rows?.map((row) => row.values["system.fides_key"])),
    [rows]
  );
  const datamapBySystem = useMemo(
    () =>
      rows
        ?.flatMap((row) => row.subRows)
        .flatMap((row) => row.subRows)
        .reduce((draft, obj) => {
          const key = obj.values["system.fides_key"];
          if (!draft[key]) {
            draft[key] = {
              name: obj.values["system.name"],
              description: obj.values["system.description"],
              dependencies: obj.values["system.system_dependencies"]
                ? obj.values["system.system_dependencies"].split(",")
                : [],
              id: obj.values["system.fides_key"],
            };
          }
          return draft;
        }, {} as Record<string, SystemNode>),
    [rows]
  );

  const data = useMemo(() => {
    let nodes: SystemNode[] = [];
    let links: Link[] = [];
    if (datamapBySystem) {
      nodes = Object.values(datamapBySystem);
      links = nodes.reduce(
        (acc: Link[], system: SystemNode) => [
          ...acc,
          ...(system.dependencies
            ?.filter((dependency) => datamapBySystem[dependency])
            .map((dependency: string) => ({
              source: system.id,
              target: dependency,
            })) ?? ([] as Link[])),
        ],
        []
      );
    }
    return { nodes, links };
  }, [datamapBySystem]);

  return {
    data,
    highlightedNodes: systemKeysFromFilteredRows,
  };
};

type SpatialDatamapProps = {} & SetSelectedSystemId;
const SpatialDatamap = ({ setSelectedSystemId }: SpatialDatamapProps) => {
  const { tableInstance } = useContext(DatamapTableContext);

  if (!tableInstance) {
    return null;
  }
  const { rows } = tableInstance;

  const {
    data,
    // eslint-disable-next-line react-hooks/rules-of-hooks
  } = useSpatialDatamap(rows);

  return (
    <Box boxSize="100%" minHeight="600px" position="relative">
      <CytoscapeGraph data={data} setSelectedSystemId={setSelectedSystemId} />
    </Box>
  );
};

export default SpatialDatamap;
