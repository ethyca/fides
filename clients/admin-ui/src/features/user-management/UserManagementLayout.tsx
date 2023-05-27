import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
} from "@fidesui/react";
import Link from "next/link";
import React from "react";

import Layout from "~/features/common/Layout";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

interface Props {
  title: string;
  children: React.ReactNode;
}
const Profile = ({ title, children }: Props) => (
  <Layout title="User Management">
    <Heading fontSize="2xl" fontWeight="semibold">
      User Management
      <Box mt={2} mb={7}>
        <Breadcrumb fontWeight="medium" fontSize="sm">
          <BreadcrumbItem>
            <Link href={USER_MANAGEMENT_ROUTE} passHref>
              <BreadcrumbLink href={USER_MANAGEMENT_ROUTE}>
                Management
              </BreadcrumbLink>
            </Link>
          </BreadcrumbItem>

          <BreadcrumbItem>
            <BreadcrumbLink href="#">{title}</BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
    </Heading>
    {children}
  </Layout>
);

export default Profile;
