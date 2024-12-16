import React from "react";

import Layout from "~/features/common/Layout";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

import PageHeader from "../common/PageHeader";

interface Props {
  children: React.ReactNode;
}

const Profile = ({ children }: Props) => (
  <Layout title="User Management">
    <PageHeader
      heading="Users"
      breadcrumbItems={[
        {
          title: "All users",
          href: USER_MANAGEMENT_ROUTE,
        },
        { title: "New User" },
      ]}
    />
    {children}
  </Layout>
);

export default Profile;
