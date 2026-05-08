import { Text, useModal } from "fidesui";
import { useCallback } from "react";

import {
  useLazyGetWildcardPromotionImpactQuery,
  WildcardPromotionMatch,
} from "../action-center.slice";
import { getActionModalProps } from "../fields/utils";

const renderContent = (matches: WildcardPromotionMatch[]) => (
  <>
    <Text>
      Adding this pattern will remove the following previously approved assets
      from your inventory:
    </Text>
    <ul className="ml-5 mt-2 list-disc">
      {matches.map((match) => (
        <li key={match.urn}>
          <Text>{match.name ?? match.urn}</Text>
        </li>
      ))}
    </ul>
  </>
);

/**
 * Returns a function that looks up the promotion impact for the given URNs and
 * shows a confirmation modal listing the assets that will be removed from the
 * inventory. Resolves to `true` when the caller should proceed (no matches, or
 * the user confirmed) and `false` when the user cancelled.
 */
export const useConfirmPromotion = () => {
  const modalApi = useModal();
  const [fetchImpact, { isFetching }] =
    useLazyGetWildcardPromotionImpactQuery();

  const confirmPromotion = useCallback(
    async (urnList: string[]): Promise<boolean> => {
      if (!urnList.length) {
        return true;
      }
      const { data } = await fetchImpact({ urnList });
      const matches = data?.matched_resources ?? [];
      if (!matches.length) {
        return true;
      }
      return modalApi.confirm(
        getActionModalProps("Add", renderContent(matches)),
      );
    },
    [fetchImpact, modalApi],
  );

  return { confirmPromotion, isCheckingImpact: isFetching };
};
