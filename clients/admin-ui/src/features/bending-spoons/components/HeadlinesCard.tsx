import palette from "fidesui/src/palette/palette.module.scss";
import { forwardRef } from "react";

import { HEADLINES, SERIF_FONT } from "../constants";

const HeadlinesCard = forwardRef<HTMLDivElement>((_, ref) => (
  <div
    ref={ref}
    style={{
      width: 912,
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 4,
    }}
  >
    {HEADLINES.map((item) => (
      <div
        key={item.label}
        style={{
          backgroundColor: palette.FIDESUI_OLIVE,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "48px 32px",
        }}
      >
        <div
          style={{
            fontFamily: SERIF_FONT,
            fontSize: 64,
            fontWeight: 400,
            fontStyle: "italic",
            color: "#ffffff",
            lineHeight: 1,
            letterSpacing: "-0.02em",
          }}
        >
          {item.value}
        </div>
        <div
          style={{
            fontFamily:
              "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            fontSize: 15,
            fontWeight: 400,
            color: "rgba(255,255,255,0.8)",
            marginTop: 14,
            textAlign: "center",
          }}
        >
          {item.label}
        </div>
        {item.footnote && (
          <div
            style={{
              fontSize: 11,
              color: "rgba(255,255,255,0.5)",
              fontStyle: "italic",
              marginTop: 4,
            }}
          >
            {item.footnote}
          </div>
        )}
      </div>
    ))}
  </div>
));

HeadlinesCard.displayName = "HeadlinesCard";
export default HeadlinesCard;
