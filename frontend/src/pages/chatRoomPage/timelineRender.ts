import type { TimelineItem } from "./utils";

export type TimelineRenderBlock =
  | {
      type: "standalone";
      item: Exclude<TimelineItem, { type: "day" }>;
      index: number;
    }
  | {
      type: "dayGroup";
      day: Extract<TimelineItem, { type: "day" }>;
      startIndex: number;
      endIndex: number;
    };

export const groupTimelineByDay = (
  timeline: readonly TimelineItem[],
): TimelineRenderBlock[] => {
  const blocks: TimelineRenderBlock[] = [];
  let currentDayGroup: Extract<
    TimelineRenderBlock,
    { type: "dayGroup" }
  > | null = null;

  timeline.forEach((item, index) => {
    if (item.type === "day") {
      currentDayGroup = {
        type: "dayGroup",
        day: item,
        startIndex: index + 1,
        endIndex: index + 1,
      };
      blocks.push(currentDayGroup);
      return;
    }

    if (currentDayGroup) {
      currentDayGroup.endIndex = index + 1;
      return;
    }

    blocks.push({ type: "standalone", item, index });
  });

  return blocks;
};
