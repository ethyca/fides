import {
  AntButton as Button,
  AntFlex as Flex,
  AntTable as Table,
  VStack,
} from "fidesui";
import NextLink from "next/link";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import usePrivacyNoticesTable from "~/features/privacy-notices/table/usePrivacyNoticesTable";

const EmptyTableNotice = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="no-results-notice"
    alignSelf="center"
    margin="auto"
  >
    <VStack>
      <span style={{ fontSize: "14px", fontWeight: 600 }}>
        No privacy notices found.
      </span>
      <span style={{ fontSize: "12px" }}>
        Click &quot;Add a privacy notice&quot; to add your first privacy notice
        to Fides.
      </span>
    </VStack>
    <NextLink href={`${PRIVACY_NOTICES_ROUTE}/new`} passHref legacyBehavior>
      <Button type="primary" size="small" data-testid="add-privacy-notice-btn">
        Add a privacy notice +
      </Button>
    </NextLink>
  </VStack>
);

export const PrivacyNoticesTableV2 = () => {
  const { tableProps, columns, userCanUpdate, isEmpty } =
    usePrivacyNoticesTable();

  return (
    <Flex vertical gap="middle" style={{ width: "100%" }}>
      {userCanUpdate && (
        <Flex justify="flex-end">
          <NextLink
            href={`${PRIVACY_NOTICES_ROUTE}/new`}
            passHref
            legacyBehavior
          >
            <Button type="primary" data-testid="add-privacy-notice-btn">
              Add a privacy notice +
            </Button>
          </NextLink>
        </Flex>
      )}
      {isEmpty ? (
        <EmptyTableNotice />
      ) : (
        <Table {...tableProps} columns={columns} />
      )}
    </Flex>
  );
};
