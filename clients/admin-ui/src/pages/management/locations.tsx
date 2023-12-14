import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";
import Link from "next/link";

import Layout from "~/features/common/Layout";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

const LocationsPage: NextPage = () => (
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
      <Box maxWidth="600px">
        <Text marginBottom={10} fontSize="sm">
          Select the locations that you operate in and Fides will make sure that
          you are automatically presented with the relevant regulatory
          guidelines and global frameworks for your locations.
        </Text>
        <Box>Locations</Box>
      </Box>
    </Box>
  </Layout>
);
export default LocationsPage;
