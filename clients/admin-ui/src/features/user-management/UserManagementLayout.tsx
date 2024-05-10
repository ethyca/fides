import { Heading } from "@fidesui/react";
import React from "react";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

interface Props {
  children: React.ReactNode;
}
const Profile = ({ children }: Props) => (
  <Layout title="User Management">
    <BackButton backPath={USER_MANAGEMENT_ROUTE} />
    <Heading fontSize="2xl" fontWeight="semibold">
      User Management
    </Heading>
    {children}
  </Layout>
);

export default Profile;
