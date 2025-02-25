import cytoscape from "cytoscape";
import klay from "cytoscape-klay";
import { Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import dynamic from "next/dynamic";
import React, { useContext, useEffect, useMemo, useState } from "react";

import { DatamapGraphContext } from "~/features/datamap/datamap-graph/DatamapGraphContext";
import {
  SetSelectedSystemId,
  SpatialData,
  SystemNode,
} from "~/features/datamap/types";

const CytoscapeWrapper = dynamic(() => import("react-cytoscapejs"), {
  ssr: false,
});

cytoscape.use(klay);
if (process.env.NODE_ENV !== "development") {
  cytoscape.warnings(false);
}

type UseCytoscapeGraphProps = {
  data: SpatialData;
} & SetSelectedSystemId;
const useCytoscapeGraph = ({ data }: { data: SpatialData }) => {
  const elements = useMemo(() => {
    const nodes = data.nodes.map((n) => ({
      data: {
        label: n.name,
        ...n,
      },
      grabbable: false,
      classes: "center-center multiline-auto outline",
    }));
    const links = data.links.map((l: any) => ({
      data: {
        source: l.source,
        target: l.target,
      },
    }));

    return [...nodes, ...links];
  }, [data.links, data.nodes]);

  const layoutConfig = useMemo(
    () => ({
      name: "klay",
      nodeDimensionsIncludeLabels: true,
      klay: {
        thoroughness: 20,
        borderSpacing: 100,
        direction: "DOWN",
        edgeRouting: "SPLINES",
        edgeSpacingFactor: 1.3,
      },
    }),
    [],
  );
  const backgroundColor = palette.FIDESUI_NEUTRAL_50;
  const styleSheet: cytoscape.Stylesheet[] = useMemo(
    () => [
      {
        selector: "node[label]",
        style: {
          label: "data(label)",
        },
      },
      {
        selector: "node",
        style: {
          shape: "ellipse",
          width: "45px",
          height: "45px",
          backgroundColor,
        },
      },
      {
        selector: "edge[label]",
        style: {
          label: "data(label)",
          width: 3,
        },
      },
      {
        selector: "edge",
        style: {
          "curve-style": "bezier",
          "target-arrow-shape": "triangle",
          "line-color": "#888",
          "target-arrow-color": "#888",
          opacity: 0.5,
        },
      },
      {
        selector: "node",
        style: {
          "background-image": "/images/DatabaseIcon.svg",
        },
      },

      {
        selector: "node:selected",
        style: {
          "background-image": "/images/SelectedDatabaseIcon.svg",
        },
      },
      {
        selector: ".center-center",
        style: {
          "text-valign": "center",
          "text-halign": "right",
        },
      },
      {
        selector: ".multiline-auto",
        style: {
          "text-wrap": "wrap",
          "text-max-width": "40",
        },
      },
      {
        selector: ".outline",
        style: {
          color: "#8d91b4",
          "text-outline-color": "#fff",
          "text-outline-width": 1,
        },
      },
    ],
    [backgroundColor],
  );

  return {
    elements,
    layoutConfig,
    styleSheet,
    backgroundColor,
  };
};

const CytoscapeGraph = ({
  data,
  setSelectedSystemId,
}: UseCytoscapeGraphProps) => {
  const { elements, layoutConfig, styleSheet, backgroundColor } =
    useCytoscapeGraph({ data });
  /* eslint-disable react/destructuring-assignment */
  const datamapGraphRef = useContext(DatamapGraphContext);

  const [cytoInitialized, setCytoInitialized] = useState(false);
  useEffect(() => {
    const setNode: cytoscape.EventHandler = (e) => {
      // eslint-disable-next-line no-underscore-dangle
      const node = e.target._private.data as SystemNode;
      setSelectedSystemId(node.id);
    };
    if (datamapGraphRef.current) {
      datamapGraphRef.current.on("click", "node", setNode);
      datamapGraphRef.current.on("layoutstop", () => {
        // solution found here: https://github.com/cytoscape/cytoscape.js/issues/941#issuecomment-104501028
        if (datamapGraphRef.current) {
          datamapGraphRef.current.maxZoom(2.5);
          datamapGraphRef.current.fit();
          datamapGraphRef.current.maxZoom(100);
        }
      });
    }

    return () => {
      if (datamapGraphRef.current) {
        datamapGraphRef.current.off("click", "node", setNode);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datamapGraphRef.current, setSelectedSystemId]);

  useEffect(
    () => () => {
      /*
       * This frees the cuto object when this component is removed from the DOM
       * Without this the cyto object will linger around when it should be gone.
       * IE: still be hanging around while the table view is open
       */
      datamapGraphRef.current = undefined;
    },
    [datamapGraphRef],
  );

  useEffect(() => {
    if (cytoInitialized) {
      /*
       * This is a hack to properly recalculate the layout.
       * When searching/filtering cytoscape is shifting all nodes
       * to the top left of the graph window.
       */
      datamapGraphRef.current?.layout(layoutConfig).stop();
      datamapGraphRef.current?.layout(layoutConfig).removeAllListeners();
      datamapGraphRef.current?.layout(layoutConfig);
      datamapGraphRef.current?.layout(layoutConfig).run();
    }
  }, [cytoInitialized, elements, datamapGraphRef, layoutConfig]);
  /* eslint-enable react/destructuring-assignment */

  return (
    <Box boxSize="100%" data-testid="cytoscape-graph" position="absolute">
      <Box boxSize="100%" bgColor="gray.50">
        <CytoscapeWrapper
          cy={(cy: cytoscape.Core) => {
            if (!cytoInitialized) {
              setCytoInitialized(true);
              // eslint-disable-next-line no-param-reassign
              datamapGraphRef.current = cy;
            }
          }}
          elements={elements}
          style={{ height: "100%", width: "100%", backgroundColor }}
          stylesheet={styleSheet}
          wheelSensitivity={0.085} // before changing the value, test the behavior on a mouse and a trackpad
          layout={layoutConfig}
        />
      </Box>
    </Box>
  );
};

export default React.memo(CytoscapeGraph);
