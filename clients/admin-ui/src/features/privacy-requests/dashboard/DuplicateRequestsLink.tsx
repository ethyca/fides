import { AntTypography as Typography } from "fidesui";
import Link from "next/link";
import { useRouter } from "next/router";

import { pluralize } from "~/features/common/utils";
import { useSearchPrivacyRequestsQuery } from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestStatus } from "~/types/api";

interface DuplicateRequestsLinkProps {
  className?: string;
  currentStatusFilter?: PrivacyRequestStatus[] | null;
}

/**
 * Component that displays a link to view duplicate privacy requests.
 * Only renders if there are duplicate requests and duplicates are not already being shown.
 * Fetches just 1 result to get the count.
 */
export const DuplicateRequestsLink = ({
  className,
  currentStatusFilter,
}: DuplicateRequestsLinkProps) => {
  const router = useRouter();

  const { data } = useSearchPrivacyRequestsQuery({
    status: [PrivacyRequestStatus.DUPLICATE],
    page: 1,
    size: 1,
  });

  const duplicateCount = data?.total ?? 0;

  // Don't render if we're already in the 'show duplicates' view
  if (
    currentStatusFilter?.length === 1 &&
    currentStatusFilter[0] === PrivacyRequestStatus.DUPLICATE
  ) {
    return null;
  }

  // Don't render if there are no duplicates
  if (duplicateCount === 0) {
    return null;
  }

  return (
    <Link
      href={{
        pathname: router.pathname,
        query: { status: PrivacyRequestStatus.DUPLICATE },
      }}
      passHref
      legacyBehavior
    >
      <Typography.Link
        data-testid="duplicate-requests-link"
        className={className}
      >
        View {duplicateCount} duplicate{" "}
        {pluralize(duplicateCount, "request", "requests")}
      </Typography.Link>
    </Link>
  );
};
