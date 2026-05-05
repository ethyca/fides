import { motion } from "framer-motion";
import type { ReactNode } from "react";

import BackgroundGlow from "./BackgroundGlow";
import Header, { HEADER_HEIGHT } from "./Header";
import SideNav from "./SideNav";

const RAIL_WIDTH = 64;

interface PageShellProps {
  businessUnitId?: string;
  onBusinessUnitChange?: (id: string) => void;
  children: ReactNode;
}

const PageShell = ({
  businessUnitId = "global",
  onBusinessUnitChange = () => {},
  children,
}: PageShellProps) => {
  return (
    <>
      <BackgroundGlow />
      <Header
        businessUnitId={businessUnitId}
        onBusinessUnitChange={onBusinessUnitChange}
      />
      <SideNav />
      <motion.main
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        style={{
          position: "relative",
          marginLeft: RAIL_WIDTH,
          paddingTop: HEADER_HEIGHT,
          minHeight: "100vh",
          boxSizing: "border-box",
          zIndex: 1,
        }}
      >
        {children}
      </motion.main>
    </>
  );
};

export default PageShell;
