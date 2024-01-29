import { Box, Heading, Spinner, Text } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import { LOCATIONS_ROUTE } from "~/features/common/nav/v2/routes";
import {
  selectLocationsRegulations,
  useGetLocationsRegulationsQuery,
} from "~/features/locations/locations.slice";
import RegulationManagement from "~/features/locations/RegulationManagement";

const RegulationsPage: NextPage = () => {
  // Subscribe to locations/regulations endpoint
  const { isLoading } = useGetLocationsRegulationsQuery();

  const locationsRegulations = useAppSelector(selectLocationsRegulations);

  return (
    <Layout title="Regulations">
      <Box data-testid="location-management">
        <Heading marginBottom={2} fontSize="2xl">
          Regulations
        </Heading>
        <Box>
          <Text marginBottom={4} fontSize="sm" maxWidth="600px">
            Select the regulations that apply to your organizations compliance
            requirements. The selections you make here will automatically update
            your location selections.{" "}
            <Text color="complimentary.500">
              <NextLink href={LOCATIONS_ROUTE} passHref>
                You can view your location settings here.
              </NextLink>
            </Text>
          </Text>
          <Box>
            {isLoading ? (
              <Spinner />
            ) : (
              <RegulationManagement data={locationsRegulations} />
            )}
          </Box>
        </Box>
      </Box>
    </Layout>
  );
};
export default RegulationsPage;
