import { useRouter } from "next/router";

interface UseHashNavigationProps<S extends string> {
  keys: S[];
  defaultKey?: S;
}

const useHashNavigation = <S extends string>({
  keys,
  defaultKey = keys[0],
}: UseHashNavigationProps<S>) => {
  const { asPath, query, pathname, ...router } = useRouter();
  const activeHash = keys.find((k) => k === asPath.split("#")[1]) ?? defaultKey;

  const setActiveHash = async (hash: S) => {
    if (router.isReady) {
      await router.replace(
        {
          pathname,
          query,
          hash,
        },
        undefined,
        { shallow: true },
      );
    }
  };

  return { activeHash, setActiveHash };
};

export default useHashNavigation;
