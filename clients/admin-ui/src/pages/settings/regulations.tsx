import { Spin, Typography } from "fidesui";
import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { RouterLink } from "~/features/common/nav/RouterLink";
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
      <PageHeader heading="Regulations" />
      <Typography.Paragraph className="max-w-xl pb-4">
        Select the regulations that apply to your organizations compliance
        requirements. The selections you make here will automatically update
        your location selections.
        <br />
        <RouterLink href={LOCATIONS_ROUTE}>
          View your location settings
        </RouterLink>
      </Typography.Paragraph>
      {isLoading ? (
        <Spin />
      ) : (
        <RegulationManagement data={locationsRegulations} />
      )}
    </Layout>
  );
};
export default RegulationsPage;
