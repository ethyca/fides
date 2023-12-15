import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Spinner,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";
import Link from "next/link";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
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
        <Breadcrumb fontWeight="medium" fontSize="sm" mb="4">
          <BreadcrumbItem>
            <Link href={USER_MANAGEMENT_ROUTE} passHref>
              <BreadcrumbLink href={USER_MANAGEMENT_ROUTE}>
                Management
              </BreadcrumbLink>
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <BreadcrumbLink href="#">Locations</BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>
        <Box>
          <Text marginBottom={4} fontSize="sm">
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
