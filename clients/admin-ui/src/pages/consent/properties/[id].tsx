import { Box, Heading } from "@fidesui/react";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import { useGetPropertyByKeyQuery } from "~/features/properties/property.slice";
import PropertyForm from "~/features/properties/PropertyForm";

const EditPropertyPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const { data } = useGetPropertyByKeyQuery(id as string);

  if (!data) {
    return null;
  }

  return (
    <Layout title={data.name}>
      <BackButton backPath={PROPERTIES_ROUTE} />
      <Box display="flex" alignItems="center" data-testid="header">
        <Heading fontSize="2xl" fontWeight="semibold">
          {data.name}
        </Heading>
      </Box>
      <Box maxWidth="720px">
        <PropertyForm property={data} />
      </Box>
    </Layout>
  );
};

export default EditPropertyPage;
