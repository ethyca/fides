import { Heading } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

import Layout from "~/features/common/Layout";

const DataSets: NextPage = () => (
  <Layout title="Datasets">
    <Heading mb={8} fontSize="2xl" fontWeight="semibold">
      Datasets
    </Heading>
  </Layout>
);

export default DataSets;
