import { Document, Font } from "@react-pdf/renderer";
import BasierSquareMedium from "fidesui/src/fonts/basier-square-medium.ttf";
import BasierSquareRegular from "fidesui/src/fonts/basier-square-regular.ttf";
import Eliza from "fidesui/src/fonts/eliza-medium.ttf";
import ElizaItalic from "fidesui/src/fonts/eliza-medium-italic.ttf";

// Register fonts
Font.register({
  family: "Eliza",
  fonts: [{ src: Eliza }, { src: ElizaItalic, fontStyle: "italic" }],
});
Font.register({
  family: "BasierSquare",
  fonts: [
    { src: BasierSquareRegular, fontStyle: "normal" },
    { src: BasierSquareMedium, fontStyle: "normal", fontWeight: "medium" },
  ],
});

export const PdfWrapper = (props: React.ComponentProps<typeof Document>) => (
  <Document {...props} />
);
