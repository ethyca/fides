import React from "react";

export const useSidePanelSlots = (children: React.ReactNode) => {
  return React.useMemo(() => {
    return React.Children.toArray(children)
      .filter(React.isValidElement)
      .sort((a, b) => {
        const orderA = (a.type as any).slotOrder ?? 99;
        const orderB = (b.type as any).slotOrder ?? 99;
        return orderA - orderB;
      });
  }, [children]);
};
