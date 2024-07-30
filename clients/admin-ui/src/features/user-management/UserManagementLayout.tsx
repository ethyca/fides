import { Heading } from "fidesui";
import React from "react";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

interface Props {
  children: React.ReactNode;
  isNewOpenIDUser: boolean;
}

const Profile = ({ children, isNewOpenIDUser }: Props) => (
  <Layout title="User Management">
    <BackButton backPath={USER_MANAGEMENT_ROUTE} />
    <Heading fontSize="2xl" fontWeight="semibold">
      {isNewOpenIDUser ? "Add new OpenID user" : "Add new user"}
    </Heading>
    {children}
  </Layout>
);

export default Profile;
