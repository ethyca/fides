import { motion } from "framer-motion";

import { SURFACE_BASE } from "./glass";

const BLOB_BLUR = "blur(180px)";

const BackgroundGlow = () => {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: SURFACE_BASE,
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: 0,
      }}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 110, ease: "linear", repeat: Infinity }}
        style={{
          position: "absolute",
          width: "220vmax",
          height: "140vmax",
          left: "-110vmax",
          top: "-90vmax",
          borderRadius: "50%",
          background: "#FAFAFA",
          filter: BLOB_BLUR,
          transformOrigin: "60% 65%",
          willChange: "transform",
        }}
      />
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 80, ease: "linear", repeat: Infinity }}
        style={{
          position: "absolute",
          width: "220vmax",
          height: "140vmax",
          right: "-110vmax",
          bottom: "-90vmax",
          borderRadius: "50%",
          background: "#F1EFEE",
          filter: BLOB_BLUR,
          transformOrigin: "40% 35%",
          willChange: "transform",
        }}
      />
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 140, ease: "linear", repeat: Infinity }}
        style={{
          position: "absolute",
          width: "200vmax",
          height: "130vmax",
          right: "-90vmax",
          top: "-80vmax",
          borderRadius: "50%",
          background: "#ffffff",
          opacity: 0.45,
          filter: BLOB_BLUR,
          transformOrigin: "35% 70%",
          willChange: "transform",
        }}
      />
    </div>
  );
};

export default BackgroundGlow;
