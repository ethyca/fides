import { Drawer, List, Spin, Typography } from "fidesui";
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

  // Drop the current request from results — the user is already viewing it.
  const otherRequests = useMemo<PrivacyRequestResponse[]>(() => {
    const items = (data?.items ?? []) as PrivacyRequestResponse[];
    return items.filter((item) => item.id !== currentRequestId);
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
        Showing other requests that match this request&apos;s{" "}
        <Typography.Text strong>
          {formatLabelList(identityFields?.labels ?? []).toLocaleLowerCase()}
        </Typography.Text>
        , including any that were marked as duplicates.
      </Typography.Paragraph>
      <Spin spinning={isFetching} centered={false}>
        <List<PrivacyRequestResponse>
          data-testid="related-requests-drawer-list"
          dataSource={otherRequests}
          locale={{ emptyText: "No other related requests found." }}
          renderItem={(item) => (
            <ListItem
              item={item}
              showActions={false}
              compact
              header={{
                link: { target: "_blank", rel: "noopener noreferrer" },
              }}
            />
          )}
        />
      </Spin>
    </Drawer>
  );
};

export default RelatedRequestsDrawer;
