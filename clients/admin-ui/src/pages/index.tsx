import { Flex, Heading, Spacer } from "@fidesui/react";
import type { NextPage } from "next";
import dynamic from "next/dynamic";
import RequestFilters from "privacy-requests/RequestFilters";
import RequestTable from "privacy-requests/RequestTable";
import { useEffect } from "react";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { Flags } from "react-feature-flags";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  selectPrivacyRequestFilters,
  setRetryRequests,
  useGetAllPrivacyRequestsQuery,
} from "~/features/privacy-requests";
import { useDSRAlert } from "~/features/privacy-requests/hooks/useDSRAlert";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> }
);

const Home: NextPage = () => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector(selectPrivacyRequestFilters);
  const { data, isFetching } = useGetAllPrivacyRequestsQuery(filters);
  const { processingErrorsAlert } = useDSRAlert(data?.items);

  useEffect(() => {
    if (isFetching && filters.status?.includes("error")) {
      dispatch(setRetryRequests({ checkAll: false, errorRequests: [] }));
    }
    processingErrorsAlert();
  }, [dispatch, filters.status, isFetching, processingErrorsAlert]);

  return (
    <Layout title="Privacy Requests">
      <Flex>
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Privacy Requests
        </Heading>
        <Spacer />
        <Flags
          authorizedFlags={["configureAlertsFlag"]}
          renderOn={() => <ActionButtons />}
        />
      </Flex>
      <RequestFilters />
      <RequestTable data={data} isFetching={isFetching} />
    </Layout>
  );
};

export default Home;
