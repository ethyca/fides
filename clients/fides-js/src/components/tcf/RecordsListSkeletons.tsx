interface Props {
  rows?: number;
}

export const RecordsListSkeletons = ({ rows = 3 }: Props) => {
  return (
    <div className="fides-notice-toggle" data-testid="records-list-skeletons">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          className="fides-data-toggle-skeleton__container"
          // eslint-disable-next-line react/no-array-index-key
          key={`fides-skeleton-bar-${index}`}
        >
          <div className="fides-skeleton__component fides-skeleton__text" />
          <div className="fides-skeleton__component fides-skeleton__switch" />
        </div>
      ))}
    </div>
  );
};
