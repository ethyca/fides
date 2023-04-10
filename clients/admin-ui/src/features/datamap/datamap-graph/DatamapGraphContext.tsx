import cytoscape from "cytoscape";
import React, {
  createContext,
  createRef,
  MutableRefObject,
  ReactNode,
} from "react";

const datamapGraphRef = createRef() as MutableRefObject<
  cytoscape.Core | undefined
>;
export const DatamapGraphContext = createContext(datamapGraphRef);

const DatamapGraphStore = ({ children }: { children: ReactNode }) => (
  <DatamapGraphContext.Provider value={datamapGraphRef}>
    {children}
  </DatamapGraphContext.Provider>
);

export default DatamapGraphStore;
