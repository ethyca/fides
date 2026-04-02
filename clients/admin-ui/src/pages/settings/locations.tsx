import { ChakraText as Text, Spin } from "fidesui";
import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import LocationManagement from "~/features/locations/LocationManagement";
import {
  selectLocationsRegulations,
  useGetLocationsRegulationsQuery,
} from "~/features/locations/locations.slice";

const LocationsPage: NextPage = () => {
  // Subscribe to locations/regulations endpoint
  const { isLoading, error } = useGetLocationsRegulationsQuery();

  const locationsRegulations = useAppSelector(selectLocationsRegulations);

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching locations settings"
      />
    );
  }

  return (
    <Layout title="Locations">
      <PageHeader heading="Locations" />
      <Text fontSize="sm" maxWidth="720px" pb={6}>
        Select the locations that you operate in and Fides will make sure that
        you are automatically presented with the relevant regulatory guidelines
        and global frameworks for your locations.
      </Text>
      {isLoading ? (
        <Spin />
      ) : (
        <LocationManagement data={locationsRegulations} />
      )}
    </Layout>
  );
};
export default LocationsPage;
