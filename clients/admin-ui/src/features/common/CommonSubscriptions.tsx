import { useAppSelector } from "~/app/hooks";
import { useFlags } from "~/features/common/features";
import { useGetHealthQuery } from "~/features/common/health.slice";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { useGetHealthQuery as useGetPlusHealthQuery } from "~/features/plus/plus.slice";
import { useGetMyRBACPermissionsQuery } from "~/features/rbac/rbac.slice";
import { useGetSystemsQuery } from "~/features/system";
import { selectThisUsersScopes } from "~/features/user-management";

const useCommonSubscriptions = () => {
  const { flags } = useFlags();

  useGetHealthQuery();
  useGetPlusHealthQuery();
  useGetSystemsQuery({ page: 1, size: 1 }); // used to preload systems count on selectSystemsCount
  useAppSelector(selectThisUsersScopes);
  useGetConfigurationSettingsQuery({ api_set: false });

  // Fetch RBAC permissions when RBAC management is enabled
  // This populates the cache so selectThisUsersScopes can use it
  useGetMyRBACPermissionsQuery(undefined, { skip: !flags.rbacManagement });
};

/**
 * This component exists only to subscribe RTK Queries whose data should be available on _every
 * page_. To add a global subscription, update the `useCommonSubscriptions` hook.
 *
 * To access the data from these queries, select the data from query's cache. More info on this
 * pattern:
 * https://redux.js.org/tutorials/essentials/part-8-rtk-query-advanced#selecting-users-data
 */
const CommonSubscriptions = () => {
  useCommonSubscriptions();

  return null;
};

export default CommonSubscriptions;
