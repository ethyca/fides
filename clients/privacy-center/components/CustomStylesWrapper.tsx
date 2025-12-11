"use client";

import { ReactNode } from "react";

import { useStyles } from "~/features/common/styles.slice";

const CustomStylesWrapper = ({
  children,
  nonce,
}: {
  children: ReactNode;
  nonce: string | null;
}) => {
  const styles = useStyles();

  return (
    <>
      {styles ? (
        <style nonce={nonce ?? undefined} suppressHydrationWarning>
          {styles}
        </style>
      ) : null}
      {children}
    </>
  );
};
export default CustomStylesWrapper;
