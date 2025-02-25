"use client";

import { ReactNode } from "react";

import { useStyles } from "~/features/common/styles.slice";

const CustomStylesWrapper = ({ children }: { children: ReactNode }) => {
  const styles = useStyles();

  return (
    <>
      {styles ? <style suppressHydrationWarning>{styles}</style> : null}
      {children}
    </>
  );
};
export default CustomStylesWrapper;
