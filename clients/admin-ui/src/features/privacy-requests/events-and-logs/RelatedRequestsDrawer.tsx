import { CUSTOM_TAG_COLOR, Drawer, List, Spin, Tag, Typography } from "fidesui";
import React, { useMemo } from "react";

import { useSearchPrivacyRequestsQuery } from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestResponse } from "~/types/api";

import { ListItem } from "../dashboard/list-item/ListItem";
import {
  extractIdentityFields,
  formatLabelList,
} from "./relatedRequestsDrawerUtils";

type RelatedRequestsDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  privacyRequest: PrivacyRequestEntity;
};

const RelatedRequestsDrawer = ({
  isOpen,
  onClose,
  privacyRequest,
}: RelatedRequestsDrawerProps) => {
  const identityFields = useMemo(
    () => extractIdentityFields(privacyRequest.identity),
    [privacyRequest.identity],
  );
  const currentRequestId = privacyRequest.id;

  const { data, isFetching } = useSearchPrivacyRequestsQuery(
    {
      identities: identityFields?.filter,
      page: 1,
      size: 100,
    },
    { skip: !isOpen || !identityFields },
  );

  // Pin the current request to the top so it's visible in context, then
  // preserve the API's default ordering for everything else.
  const sortedRequests = useMemo<PrivacyRequestResponse[]>(() => {
    const items = (data?.items ?? []) as PrivacyRequestResponse[];
    return [...items].sort((a, b) => {
      if (a.id === currentRequestId) {
        return -1;
      }
      if (b.id === currentRequestId) {
        return 1;
      }
      return 0;
    });
  }, [data, currentRequestId]);

  return (
    <Drawer
      open={isOpen}
      onClose={onClose}
      width={640}
      autoFocus={false}
      destroyOnHidden
      title="Related requests"
    >
      <Typography.Paragraph type="secondary" className="!mb-4">
        Showing all requests that match this request&apos;s{" "}
        <Typography.Text strong>
          {formatLabelList(identityFields?.labels ?? []).toLocaleLowerCase()}
        </Typography.Text>
        , including any that were marked as duplicates.
      </Typography.Paragraph>
      <Spin spinning={isFetching} centered={false}>
        <List<PrivacyRequestResponse>
          data-testid="related-requests-drawer-list"
          dataSource={sortedRequests}
          locale={{ emptyText: "No matching requests found." }}
          renderItem={(item) => (
            <ListItem
              item={item}
              showActions={false}
              compact
              header={{
                link: { target: "_blank", rel: "noopener noreferrer" },
                extraTags:
                  item.id === currentRequestId ? (
                    <Tag color={CUSTOM_TAG_COLOR.INFO}>Current</Tag>
                  ) : undefined,
              }}
            />
          )}
        />
      </Spin>
    </Drawer>
  );
};

export default RelatedRequestsDrawer;
