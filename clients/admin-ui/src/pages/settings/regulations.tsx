import { Box, Link, Spinner, Text } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import { LOCATIONS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
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
      <Box data-testid="regulation-management">
        <PageHeader heading="Regulations" />
        <Text pb={6} fontSize="sm" maxWidth="600px">
          Select the regulations that apply to your organizations compliance
          requirements. The selections you make here will automatically update
          your location selections.{" "}
          <Link as={NextLink} href={LOCATIONS_ROUTE} color="complimentary.500">
            You can view your location settings here.
          </Link>
        </Text>
        <Box>
          {isLoading ? (
            <Spinner />
          ) : (
            <RegulationManagement data={locationsRegulations} />
          )}
        </Box>
      </Box>
    </Layout>
  );
};
export default RegulationsPage;
