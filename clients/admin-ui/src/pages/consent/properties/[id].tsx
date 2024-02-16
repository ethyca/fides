import { Box, Heading } from "@fidesui/react";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import PropertyForm from "~/features/properties/PropertyForm";

const Header = () => (
  <Box display="flex" alignItems="center" data-testid="header">
    <Heading fontSize="2xl" fontWeight="semibold">
      Edit property
    </Heading>
  </Box>
);

const AddPropertyPage: NextPage = () => (
  <Layout title="Edit property">
    <BackButton backPath={PROPERTIES_ROUTE} />
    <Header />
    <Box maxWidth="720px">
      <PropertyForm />
    </Box>
  </Layout>
);

export default AddPropertyPage;
