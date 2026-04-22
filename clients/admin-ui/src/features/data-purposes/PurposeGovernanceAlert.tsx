import { Alert, Button, Flex, Icons, useMessage } from "fidesui";
import { useMemo } from "react";

import { isErrorResult } from "~/features/common/helpers";

import {
  useAcceptPurposeCategoriesMutation,
  useGetDataPurposeByKeyQuery,
  useGetPurposeCoverageQuery,
  useGetPurposeDatasetsQuery,
} from "./data-purpose.slice";

interface PurposeGovernanceAlertProps {
  fidesKey: string;
}

/**
 * Governance insight describing drift between defined and detected categories
 * on the purpose. Uses the `agent` alert variant so the surfaced finding
 * reads as an AI/automation callout rather than a system notification.
 */
const PurposeGovernanceAlert = ({ fidesKey }: PurposeGovernanceAlertProps) => {
  const message = useMessage();
  const { data: purpose } = useGetDataPurposeByKeyQuery(fidesKey);
  const { data: coverage } = useGetPurposeCoverageQuery(fidesKey);
  const { data: datasets = [] } = useGetPurposeDatasetsQuery(fidesKey);
  const [acceptCategories, { isLoading: isAccepting }] =
    useAcceptPurposeCategoriesMutation();

  const definedSet = useMemo(
    () => new Set(purpose?.data_categories ?? []),
    [purpose?.data_categories],
  );

  const undeclared = useMemo(() => {
    const seen = new Set<string>();
    datasets.forEach((d) => {
      d.data_categories.forEach((c) => {
        if (!definedSet.has(c)) {
          seen.add(c);
        }
      });
    });
    return Array.from(seen);
  }, [datasets, definedSet]);

  const contributingSystems = useMemo(() => {
    const names = new Set<string>();
    datasets.forEach((d) => {
      if (d.data_categories.some((c) => !definedSet.has(c))) {
        names.add(d.system_name);
      }
    });
    return Array.from(names);
  }, [datasets, definedSet]);

  const additionalUndeclared = useMemo(
    () =>
      (coverage?.detected_data_categories ?? []).filter(
        (c) => !definedSet.has(c) && !undeclared.includes(c),
      ),
    [coverage?.detected_data_categories, definedSet, undeclared],
  );

  const allUndeclared = [...undeclared, ...additionalUndeclared];

  const handleApprove = async () => {
    const result = await acceptCategories({
      fidesKey,
      categories: allUndeclared,
    });
    if (isErrorResult(result)) {
      message.error("Could not approve categories");
      return;
    }
    message.success(
      allUndeclared.length === 1
        ? `Added "${allUndeclared[0]}" to defined categories`
        : `Added ${allUndeclared.length} categories to defined list`,
    );
  };

  if (allUndeclared.length === 0) {
    return null;
  }

  return (
    <Alert
      type="agent"
      showIcon
      closable
      title="Governance insight"
      description={
        <Flex align="center" gap={8}>
          <span>
            {allUndeclared.length}{" "}
            {allUndeclared.length === 1 ? "category was" : "categories were"}{" "}
            detected in{" "}
            {contributingSystems.length > 0 ? (
              <>
                {contributingSystems.map((s, i) => (
                  <span key={s}>
                    {i > 0 && ", "}
                    {s}
                  </span>
                ))}{" "}
              </>
            ) : null}
            that {allUndeclared.length === 1 ? "is not" : "are not"} defined on
            this purpose.
          </span>
          <Button
            size="small"
            type="text"
            icon={<Icons.Checkmark size={14} />}
            onClick={handleApprove}
            loading={isAccepting}
            style={{ whiteSpace: "nowrap" }}
          >
            Approve {allUndeclared.length === 1 ? "category" : "categories"}
          </Button>
        </Flex>
      }
    />
  );
};

export default PurposeGovernanceAlert;
