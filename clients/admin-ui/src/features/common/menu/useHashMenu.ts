import { AntMenuProps as MenuProps } from "fidesui";
import { ReactNode } from "react";

import useHashNavigation from "../hooks/useHashNavigation";

type MenuItem = NonNullable<MenuProps["items"]>[number];

interface UseHashMenuProps<S extends string> {
  keys: S[];
  items: Record<
    S,
    MenuItem & {
      key: S;
      renderRoute: () => ReactNode;
    }
  >;
  defaultKey?: S;
}

const useHashMenu = <S extends string>({
  keys,
  defaultKey,
  items,
}: UseHashMenuProps<S>) => {
  const { activeHash, setActiveHash } = useHashNavigation({ keys, defaultKey });

  return {
    activeMenuItem: items[activeHash],
    setActiveTab: setActiveHash,
  };
};

export default useHashMenu;
