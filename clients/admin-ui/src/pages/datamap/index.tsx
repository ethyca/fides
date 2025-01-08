import type { NextPage } from "next";
import React, { useMemo } from "react";

import { DirtyFormConfirmationModal } from "~/features/common/hooks/useIsAnyFormDirty";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import Datamap from "~/features/datamap/Datamap";
import DatamapGraphStore from "~/features/datamap/datamap-graph/DatamapGraphContext";
import DatamapTableContext, {
  DatamapTableContextValue,
} from "~/features/datamap/datamap-table/DatamapTableContext";

const Home: NextPage = () => {
  const datamapTableContextValue = useMemo(
    () => new DatamapTableContextValue(),
    [],
  );

  return (
    <Layout
      title="Data lineage"
      mainProps={{
        padding: "24px 0 0 40px",
      }}
    >
      <PageHeader heading="Data lineage" />
      <DatamapTableContext.Provider value={datamapTableContextValue}>
        <DatamapGraphStore>
          <Datamap />
          <DirtyFormConfirmationModal />
        </DatamapGraphStore>
      </DatamapTableContext.Provider>
    </Layout>
  );
};

export default Home;
