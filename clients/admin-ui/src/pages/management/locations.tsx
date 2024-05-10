import { Box, Heading, Spinner, Text } from "@fidesui/react";
import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
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
        <Heading marginBottom={2} fontSize="2xl">
          Locations
        </Heading>
        <Box>
          <Text marginBottom={4} fontSize="sm" maxWidth="720px">
            Select the locations that you operate in and Fides will make sure
            that you are automatically presented with the relevant regulatory
            guidelines and global frameworks for your locations.
          </Text>
          <Box>
            {isLoading ? (
              <Spinner />
            ) : (
              <LocationManagement data={locationsRegulations} />
            )}
          </Box>
        </Box>
      </Box>
    </Layout>
  );
};
export default LocationsPage;
