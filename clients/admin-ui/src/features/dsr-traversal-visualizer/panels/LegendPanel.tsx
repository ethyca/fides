import styles from "./LegendPanel.module.scss";

const LegendPanel = () => (
  <div className={styles.root} data-testid="legend-panel">
    <div className={styles.row}>
      <svg className={styles.swatch} viewBox="0 0 30 8">
        <line x1="0" y1="4" x2="30" y2="4" stroke="#1d4ed8" strokeWidth="2" />
      </svg>
      <span>Data dependency</span>
    </div>
    <div className={styles.row}>
      <svg className={styles.swatch} viewBox="0 0 30 8">
        <line x1="0" y1="4" x2="30" y2="4" stroke="#b45309" strokeWidth="2" strokeDasharray="6 4" />
      </svg>
      <span>Manual review gate</span>
    </div>
    <div className={styles.row}>
      <span className={`${styles.cardSwatch} ${styles.cardInFlow}`} />
      <span>In-flow system</span>
    </div>
    <div className={styles.row}>
      <span className={`${styles.cardSwatch} ${styles.cardSkipped}`} />
      <span>Not touched</span>
    </div>
    <div className={styles.row}>
      <span className={styles.chevron}>›</span>
      <span>Process flow</span>
    </div>
  </div>
);

export default LegendPanel;
