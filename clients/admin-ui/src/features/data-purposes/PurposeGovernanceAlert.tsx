import { Alert, Button, Flex, Icons, useMessage } from "fidesui";
import { useMemo } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { pluralize } from "~/features/common/utils";

import {
  type PurposeDatasetAssignment,
  useAcceptPurposeCategoriesMutation,
  useGetPurposeOverviewQuery,
} from "./data-purpose.slice";

interface PurposeGovernanceAlertProps {
  fidesKey: string;
}

const EMPTY_DATASETS: PurposeDatasetAssignment[] = [];

/**
 * Governance insight describing drift between defined and detected categories
 * on the purpose. Uses the `agent` alert variant so the surfaced finding
 * reads as an AI/automation callout rather than a system notification.
 *
 * The authoritative source of undeclared categories is the assigned datasets,
 * not coverage.detected_data_categories — coverage is a rolled-up summary that
 * can drift from dataset truth. Deriving here keeps a single source.
 */
const PurposeGovernanceAlert = ({ fidesKey }: PurposeGovernanceAlertProps) => {
  const message = useMessage();
  const { data: overview } = useGetPurposeOverviewQuery(fidesKey);
  const purpose = overview?.purpose;
  const datasets = overview?.datasets ?? EMPTY_DATASETS;
  const [acceptCategories, { isLoading: isAccepting }] =
    useAcceptPurposeCategoriesMutation();

  const definedSet = useMemo(
    () => new Set(purpose?.data_categories ?? []),
    [purpose?.data_categories],
  );

  const { undeclared, contributingSystems } = useMemo(() => {
    const seenCategories = new Set<string>();
    const seenSystems = new Set<string>();
    datasets.forEach((dataset) => {
      const datasetUndeclared = dataset.data_categories.filter(
        (category) => !definedSet.has(category),
      );
      if (datasetUndeclared.length === 0) {
        return;
      }
      datasetUndeclared.forEach((category) => seenCategories.add(category));
      seenSystems.add(dataset.system_name);
    });
    return {
      undeclared: Array.from(seenCategories),
      contributingSystems: Array.from(seenSystems),
    };
  }, [datasets, definedSet]);

  const handleApprove = async () => {
    const result = await acceptCategories({
      fidesKey,
      categories: undeclared,
    });
    if (isErrorResult(result)) {
      message.error("Could not approve categories");
      return;
    }
    message.success(
      pluralize(
        undeclared.length,
        `Added "${undeclared[0]}" to defined categories`,
        `Added ${undeclared.length} categories to defined list`,
      ),
    );
  };

  if (undeclared.length === 0) {
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
            {undeclared.length}{" "}
            {pluralize(undeclared.length, "category was", "categories were")}{" "}
            detected in{" "}
            {contributingSystems.length > 0 ? (
              <>
                {contributingSystems.map((systemName, index) => (
                  <span key={systemName}>
                    {index > 0 && ", "}
                    {systemName}
                  </span>
                ))}{" "}
              </>
            ) : null}
            that {pluralize(undeclared.length, "is not", "are not")} defined on
            this purpose.
          </span>
          <Button
            size="small"
            type="text"
            icon={<Icons.Checkmark size={14} />}
            onClick={handleApprove}
            loading={isAccepting}
            className="whitespace-nowrap"
          >
            Approve {pluralize(undeclared.length, "category", "categories")}
          </Button>
        </Flex>
      }
    />
  );
};

export default PurposeGovernanceAlert;
