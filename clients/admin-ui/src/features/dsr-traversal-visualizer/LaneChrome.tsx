import { useViewport } from "@xyflow/react";
import classNames from "classnames";
import { Tooltip } from "fidesui";
import { CSSProperties } from "react";

import { CARD_PITCH, LANE_PADDING_X, STAGE_GAP_HORIZONTAL } from "./constants";
import styles from "./LaneChrome.module.scss";
import { LaneBounds, LaneId } from "./types";

interface Props {
  lanes: LaneBounds[];
  onToggleCollapse: (lane: LaneId) => void;
}

export const LaneChrome = ({ lanes, onToggleCollapse }: Props) => {
  // Apply React Flow's current pan + zoom so lane chrome moves in sync with
  // the nodes positioned in the same canvas coord space.
  const { x: vx, y: vy, zoom } = useViewport();
  const viewportTransform: CSSProperties = {
    transform: `translate(${vx}px, ${vy}px) scale(${zoom})`,
    transformOrigin: "0 0",
    position: "absolute",
    inset: 0,
    pointerEvents: "none",
  };
  return (
    <>
      <div className={styles.root} aria-hidden="false">
        <div style={viewportTransform}>
          {lanes
            .filter((lane) => !lane.hidden)
            .map((lane) => {
              const style: CSSProperties = {
                left: lane.x,
                top: lane.y,
                width: lane.width,
                height: lane.height,
              };
              return (
                <div
                  key={lane.id}
                  className={classNames(
                    styles.lane,
                    styles[`lane-${lane.id}`],
                    {
                      [styles.collapsed]: lane.collapsed,
                      [styles.outOfFlow]: lane.outOfFlow,
                    },
                  )}
                  style={style}
                  data-testid={`lane-${lane.id}`}
                  data-collapsed={lane.collapsed ? "true" : "false"}
                >
                  <div className={styles.header}>
                    <Tooltip title={lane.tooltip} placement="top">
                      <span className={styles.label}>{lane.label}</span>
                    </Tooltip>
                    <span className={styles.count}>{lane.cardCount}</span>
                    {/* Visual chevron only — the click target is in the
                      separate `toggleLayer` below so it can sit above
                      React Flow's pane. */}
                    <span className={styles.toggle} aria-hidden="true">
                      {lane.collapsed ? "›" : "‹"}
                    </span>
                  </div>

                  {!lane.collapsed &&
                    lane.stages &&
                    (() => {
                      const { stages } = lane;
                      const tallestRows = stages.reduce(
                        (n, s) => Math.max(n, s.nodeIds.length / s.columns),
                        0,
                      );
                      return stages.map((stage, stageIdx) => {
                        // Sub-header: positioned above the stage's card grid,
                        // sized to the stage's grid width.
                        const headerStyle: CSSProperties = {
                          position: "absolute",
                          left: LANE_PADDING_X + stage.xStart,
                          top: stage.headerY,
                          width: stage.width,
                        };
                        const isLast = stageIdx === stages.length - 1;
                        // Vertically centered on the grid baseline;
                        // `transform: translate(-50%, -50%)` in `.stageChevron`
                        // recenters the element on this anchor.
                        const chevronTop =
                          stage.gridY +
                          Math.ceil(tallestRows) * (CARD_PITCH / 2);
                        return (
                          <div key={stage.index}>
                            <div className={styles.stage} style={headerStyle}>
                              <Tooltip title={stage.tooltip} placement="top">
                                <span className={styles.stageLabel}>
                                  <span className={styles.stageNum}>
                                    {stage.index}
                                  </span>
                                  {stage.label}
                                </span>
                              </Tooltip>
                            </div>
                            {!isLast && (
                              <div
                                className={styles.stageChevron}
                                style={{
                                  left:
                                    LANE_PADDING_X +
                                    stage.xEnd +
                                    STAGE_GAP_HORIZONTAL / 2,
                                  top: chevronTop,
                                }}
                                data-testid={`stage-chevron-${stage.index}`}
                              >
                                ›
                              </div>
                            )}
                          </div>
                        );
                      });
                    })()}

                  {!lane.collapsed && lane.outOfFlow && (
                    <span className={styles.outOfFlowBadge}>Not in flow</span>
                  )}
                </div>
              );
            })}

          {/* Flow rails connecting in-flow lanes */}
          {lanes.map((lane, idx) => {
            if (lane.outOfFlow || lane.hidden || idx === lanes.length - 1) {
              return null;
            }
            const next = lanes[idx + 1];
            if (next.outOfFlow || next.hidden) {
              return null;
            }
            return (
              <div
                key={`rail-${lane.id}-${next.id}`}
                className={styles.rail}
                style={{
                  left: lane.x + lane.width,
                  top: lane.y + 24,
                  width: next.x - (lane.x + lane.width),
                }}
                data-testid={`rail-${lane.id}-${next.id}`}
              >
                <span className={styles.chevron}>›</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Floating click-target layer for collapse toggles. Sibling of
        `.root` so it has its own stacking context above React Flow's
        pane. Wrapper is non-interactive; only the per-button hit area
        captures clicks (small enough not to block cards beneath). */}
      <div className={styles.toggleLayer}>
        <div style={viewportTransform}>
          {lanes
            .filter((lane) => !lane.hidden)
            .map((lane) => (
              <button
                key={`toggle-${lane.id}`}
                type="button"
                className={styles.floatingToggle}
                style={{
                  left: lane.x + lane.width - 28,
                  top: lane.y + 6,
                }}
                aria-label={
                  lane.collapsed
                    ? `Expand ${lane.label} lane`
                    : `Collapse ${lane.label} lane`
                }
                data-testid={`lane-${lane.id}-toggle`}
                onClick={() => onToggleCollapse(lane.id)}
              >
                {lane.collapsed ? "›" : "‹"}
              </button>
            ))}
        </div>
      </div>
    </>
  );
};
