import { Box, List, ListItem, Text } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";

import {
  selectAllPrivacyNotices,
  selectPage,
  selectPageSize,
  useGetAllPrivacyNoticesQuery,
} from "./privacy-notices.slice";

const PrivacyNoticesTable = () => {
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);

  if (privacyNotices.length === 0) {
    return <Text>No privacy notices found.</Text>;
  }

  return (
    <Box>
      <List>
        {privacyNotices.map((notice) => (
          <ListItem key={notice.id}>{notice.name}</ListItem>
        ))}
      </List>
    </Box>
  );
};

export default PrivacyNoticesTable;
