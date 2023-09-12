import { ButtonGroup, Center, Spinner, Text, VStack } from "@fidesui/react";

import EmptyTableState from "~/features/common/table/EmptyTableState";
import { useGetAllSystemsQuery } from "~/features/system";

import AddCookie from "./AddCookie";
import AddVendor from "./AddVendor";
import VendorCookieTable from "./VendorCookieTable";

const AddButtons = ({ includeCookies }: { includeCookies?: boolean }) => (
  <ButtonGroup size="sm" colorScheme="primary">
    <AddVendor />
    {includeCookies ? <AddCookie /> : null}
  </ButtonGroup>
);

const EmptyStateContent = () => (
  <VStack spacing={4} alignItems="start">
    <Text>
      To manage consent, please add your first vendor. A vendor is a third-party
      SaaS application that processes personal data for varying purposes.
    </Text>
    <AddButtons includeCookies={false} />
  </VStack>
);

const ConfigureConsent = () => {
  const { data: allSystems, isLoading } = useGetAllSystemsQuery();

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
        description={<EmptyStateContent />}
      />
    );
  }

  return <VendorCookieTable />;
};

export default ConfigureConsent;
