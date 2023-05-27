import type { NextPage } from "next";
import React, { useMemo } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DirtyFormConfirmationModal } from "~/features/common/hooks/useIsAnyFormDirty";
import Datamap from "~/features/datamap/Datamap";
import DatamapGraphStore from "~/features/datamap/datamap-graph/DatamapGraphContext";
import DatamapTableContext, {
  DatamapTableContextValue,
} from "~/features/datamap/datamap-table/DatamapTableContext";

const Home: NextPage = () => {
  const datamapTableContextValue = useMemo(
    () => new DatamapTableContextValue(),
    []
  );

  return (
    <FixedLayout title="View Map">
      <DatamapTableContext.Provider value={datamapTableContextValue}>
        <DatamapGraphStore>
          <Datamap />
          <DirtyFormConfirmationModal />
        </DatamapGraphStore>
      </DatamapTableContext.Provider>
    </FixedLayout>
  );
};

export default Home;
