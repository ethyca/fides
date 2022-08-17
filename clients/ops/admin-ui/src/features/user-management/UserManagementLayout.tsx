import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
} from "@fidesui/react";
import Link from "next/link";
import React from "react";

import { USER_MANAGEMENT_ROUTE } from "../../constants";
import ProtectedRoute from "../auth/ProtectedRoute";
import NavBar from "../common/NavBar";

interface Props {
  title: string;
  children: React.ReactNode;
}
const Profile = ({ title, children }: Props) => (
  <ProtectedRoute>
    <div>
      <NavBar />
      <main>
        <Box px={9} py={10}>
          <Heading fontSize="2xl" fontWeight="semibold">
            User Management
            <Box mt={2} mb={7}>
              <Breadcrumb fontWeight="medium" fontSize="sm">
                <BreadcrumbItem>
                  <Link href={USER_MANAGEMENT_ROUTE} passHref>
                    <BreadcrumbLink href={USER_MANAGEMENT_ROUTE}>
                      User Management
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
        </Box>
      </main>
    </div>
  </ProtectedRoute>
);

export default Profile;
