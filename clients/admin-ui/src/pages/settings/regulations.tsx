import {
  ChakraBox as Box,
  ChakraLink as Link,
  ChakraSpinner as Spinner,
  ChakraText as Text,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
import ErrorPage from "~/features/common/errors/ErrorPage";
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
  const { isLoading, error } = useGetLocationsRegulationsQuery();

  const locationsRegulations = useAppSelector(selectLocationsRegulations);

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching regulations settings"
      />
    );
  }

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
