"use client";

import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";

const CustomStylesWrapper = ({ children }: { children: ReactNode }) => {
  const styles = useAppSelector(
    (state) => (state as any).styles?.styles as string | undefined,
  );

  return (
    <>
      {styles ? <style suppressHydrationWarning>{styles}</style> : null}
      {children}
    </>
  );
};
export default CustomStylesWrapper;
