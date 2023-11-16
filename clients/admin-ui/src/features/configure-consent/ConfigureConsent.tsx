import { Center, HStack, Spinner, Text, VStack } from "@fidesui/react";
import { FC } from "react";

import EmptyTableState from "~/features/common/table/EmptyTableState";
import AddVendor from "~/features/configure-consent/AddVendor";
import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import { useGetAllSystemsQuery } from "~/features/system";
import { useGetVendorReportQuery } from "~/features/plus/plus.slice";

import VendorCookieTable from "./VendorCookieTable";

const EmptyStateContent: FC = ({ children }) => (
  <VStack spacing={4} alignItems="start">
    <Text>
      To manage consent, please add your first vendor. A vendor is a third-party
      SaaS application that processes personal data for varying purposes.
    </Text>
    <HStack>{children}</HStack>
  </VStack>
);

const ConfigureConsent = () => {
  const { data: allSystems, isLoading } = useGetAllSystemsQuery();
  useGetAllDataUsesQuery();
  const { data: report } = useGetVendorReportQuery();
  console.log(report);

  if (isLoading) {
    return (
      <Center>
        <Spinner />
      </Center>
    );
  }

  if (!allSystems || allSystems.length === 0) {
    return (
      <EmptyTableState
        title="It looks like it's your first time here!"
        description={
          <EmptyStateContent>
            <AddVendor />
          </EmptyStateContent>
        }
      />
    );
  }

  return <VendorCookieTable />;
};

export default ConfigureConsent;
