import { Box, Spinner, Text } from "fidesui";
import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import LocationManagement from "~/features/locations/LocationManagement";
import {
  selectLocationsRegulations,
  useGetLocationsRegulationsQuery,
} from "~/features/locations/locations.slice";

const LocationsPage: NextPage = () => {
  // Subscribe to locations/regulations endpoint
  const { isLoading } = useGetLocationsRegulationsQuery();

  const locationsRegulations = useAppSelector(selectLocationsRegulations);

  return (
    <Layout title="Locations">
      <Box data-testid="location-management">
        <PageHeader heading="Locations">
          <Text fontSize="sm" maxWidth="720px">
            Select the locations that you operate in and Fides will make sure
            that you are automatically presented with the relevant regulatory
            guidelines and global frameworks for your locations.
          </Text>
        </PageHeader>
        <Box>
          {isLoading ? (
            <Spinner />
          ) : (
            <LocationManagement data={locationsRegulations} />
          )}
        </Box>
      </Box>
    </Layout>
  );
};
export default LocationsPage;
