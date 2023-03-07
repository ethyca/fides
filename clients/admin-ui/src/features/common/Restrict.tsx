import { useAppSelector } from "~/app/hooks";
import { selectThisUsersScopes } from "~/features/user-management";
import { ScopeRegistryEnum } from "~/types/api";

export const useHasPermission = (scopes: ScopeRegistryEnum[]) => {
  const userScopes = useAppSelector(selectThisUsersScopes);
  return (
    userScopes.filter((userScope) => scopes.includes(userScope)).length > 0
  );
};

const Restrict = ({
  scopes,
  children,
}: {
  /**
   * If the user has _any_ of these scopes, the children will render
   */
  scopes: ScopeRegistryEnum[];
  children: React.ReactNode;
}) => {
  const userHasScopes = useHasPermission(scopes);

  if (!userHasScopes) {
    return null;
  }
  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <>{children}</>;
};

export default Restrict;
