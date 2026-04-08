import type { NextPage } from "next";
import React, { useMemo } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import Datamap from "~/features/datamap/Datamap";
import DatamapTableContext, {
  DatamapTableContextValue,
} from "~/features/datamap/datamap-table/DatamapTableContext";
import { useDatamapTable } from "~/features/datamap/datamap-table/hooks/useDatamapTable";

const Home: NextPage = () => {
  const datamapTableContextValue = useMemo(
    () => new DatamapTableContextValue(),
    [],
  );

  const { error } = useDatamapTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your datamap"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Data lineage" />
      </SidePanel>
      <Layout
        title="Data lineage"
        mainProps={{
          padding: "24px 0 0 40px",
        }}
      >
        <DatamapTableContext.Provider value={datamapTableContextValue}>
          <Datamap />
        </DatamapTableContext.Provider>
      </Layout>
    </>
  );
};

export default Home;
