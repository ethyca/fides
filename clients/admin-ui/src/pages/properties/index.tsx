import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { Text } from "fidesui";
import type { NextPage } from "next";
import { useCallback, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { PropertiesTable } from "~/features/properties/PropertiesTable";

const PropertiesPage: NextPage = () => {
  const [error, setError] = useState<
    FetchBaseQueryError | SerializedError | null
  >(null);

  const onError = useCallback((e: FetchBaseQueryError | SerializedError) => {
    setError(e);
  }, []);

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching properties"
      />
    );
  }

  return (
    <Layout title="Properties">
      <PageHeader heading="Properties">
        <Text fontSize="sm" width={{ base: "100%", lg: "60%" }}>
          Review and manage your properties below. Properties are the locations
          you have configured for consent management such as a website or mobile
          app.
        </Text>
      </PageHeader>
      <PropertiesTable onError={onError} />
    </Layout>
  );
};

export default PropertiesPage;
