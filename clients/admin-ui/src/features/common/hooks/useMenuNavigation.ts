import { useParams } from "next/navigation";
import { useRouter } from "next/router";

interface UseMenuNavigationProps<
  Key extends string,
  Path extends string,
  R extends Record<Key, Path>,
> {
  routes: R;
  defaultKey?: Exclude<keyof R, symbol | number>;
}

const useMenuNavigation = <
  K extends string,
  P extends string,
  R extends Record<K, P>,
>({
  routes,
  defaultKey,
}: UseMenuNavigationProps<K, P, R>) => {
  const { pathname, isReady, ...router } = useRouter();
  const params = useParams();

  const activeItem =
    Object.entries(routes).find(([, p]) => p === pathname)?.[0] ?? defaultKey;

  const setActiveItem = async (nextPathKey: K) => {
    const nextPath = routes[nextPathKey];

    await router.push({
      pathname: nextPath,
      query: params,
    });
  };

  return { activeItem, setActiveItem };
};

export default useMenuNavigation;
