import {
  AntButton as Button,
  AntFlex as Flex,
  AntTable as Table,
} from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";

import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import usePrivacyNoticesTable from "~/features/privacy-notices/table/usePrivacyNoticesTable";

export const PrivacyNoticesTable = () => {
  const { tableProps, columns, userCanUpdate } = usePrivacyNoticesTable();

  const router = useRouter();

  return (
    <Flex vertical gap="middle" style={{ width: "100%" }}>
      {userCanUpdate && (
        <Flex justify="flex-end">
          <Button
            onClick={() => router.push(`${PRIVACY_NOTICES_ROUTE}/new`)}
            type="primary"
            data-testid="add-privacy-notice-btn"
          >
            Add a privacy notice +
          </Button>
        </Flex>
      )}
      <Table {...tableProps} columns={columns} />
    </Flex>
  );
};
