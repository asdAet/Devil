import { Skeleton } from "../shared/ui";

const fallbackRows = [
  { left: "8%", width: "42%" },
  { left: "18%", width: "58%" },
  { left: "10%", width: "50%" },
] as const;

export function RouteChunkFallback() {
  return (
    <div
      aria-busy="true"
      aria-live="polite"
      style={{
        display: "grid",
        gap: 12,
        minHeight: "min(420px, 55vh)",
        padding: 24,
      }}
    >
      <Skeleton height={44} radius={8} width="min(320px, 70%)" />
      <Skeleton height={140} radius={8} />
      {fallbackRows.map((row) => (
        <Skeleton
          key={`${row.left}-${row.width}`}
          height={18}
          radius={6}
          style={{ marginLeft: row.left }}
          width={row.width}
        />
      ))}
    </div>
  );
}
