import type { NextPage } from "next";
import React, { useMemo } from "react";

import { DirtyFormConfirmationModal } from "~/features/common/hooks/useIsAnyFormDirty";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import Datamap from "~/features/datamap/Datamap";
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
      <PageHeader style={{ paddingLeft: 0 }} heading="Data lineage" />
      <DatamapTableContext.Provider value={datamapTableContextValue}>
        <Datamap />
        <DirtyFormConfirmationModal />
      </DatamapTableContext.Provider>
    </Layout>
  );
};

export default Home;
