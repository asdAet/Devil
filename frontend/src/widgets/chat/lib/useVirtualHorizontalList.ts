import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";

type VirtualHorizontalListOptions = {
  gap?: number;
  itemCount: number;
  itemWidth: number;
  overscanItems?: number;
  scrollRoot: HTMLElement | null;
};

type VirtualHorizontalListItem = {
  index: number;
  style: CSSProperties;
};

type VirtualHorizontalListState = {
  scrollLeft: number;
  width: number;
};

const readListState = (node: HTMLElement): VirtualHorizontalListState => ({
  scrollLeft: Math.max(0, node.scrollLeft),
  width: Math.max(0, node.clientWidth),
});

export const useVirtualHorizontalList = ({
  gap = 0,
  itemCount,
  itemWidth,
  overscanItems = 3,
  scrollRoot,
}: VirtualHorizontalListOptions): {
  items: VirtualHorizontalListItem[];
  totalWidth: number;
} => {
  const [listState, setListState] = useState<VirtualHorizontalListState>({
    scrollLeft: 0,
    width: 0,
  });

  useEffect(() => {
    const node = scrollRoot;
    if (!node) {
      return;
    }

    let animationFrame = 0;

    const update = () => {
      animationFrame = 0;
      setListState(readListState(node));
    };

    const scheduleUpdate = () => {
      if (animationFrame !== 0) {
        return;
      }

      animationFrame = window.requestAnimationFrame(update);
    };

    update();
    node.addEventListener("scroll", scheduleUpdate, { passive: true });

    let resizeObserver: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(scheduleUpdate);
      resizeObserver.observe(node);
    } else {
      window.addEventListener("resize", scheduleUpdate);
    }

    return () => {
      if (animationFrame !== 0) {
        window.cancelAnimationFrame(animationFrame);
      }
      node.removeEventListener("scroll", scheduleUpdate);
      resizeObserver?.disconnect();
      if (typeof ResizeObserver === "undefined") {
        window.removeEventListener("resize", scheduleUpdate);
      }
    };
  }, [scrollRoot]);

  return useMemo(() => {
    const stride = itemWidth + gap;
    const totalWidth =
      itemCount > 0 ? itemCount * itemWidth + (itemCount - 1) * gap : 0;

    if (itemCount === 0 || stride <= 0) {
      return {
        items: [],
        totalWidth,
      };
    }

    const firstVisibleIndex = Math.floor(listState.scrollLeft / stride);
    const lastVisibleIndex = Math.floor(
      (listState.scrollLeft + listState.width) / stride,
    );
    const startIndex = Math.max(0, firstVisibleIndex - overscanItems);
    const endIndex = Math.min(itemCount - 1, lastVisibleIndex + overscanItems);
    const items: VirtualHorizontalListItem[] = [];

    for (let index = startIndex; index <= endIndex; index += 1) {
      items.push({
        index,
        style: {
          left: index * stride,
          position: "absolute",
          top: 0,
          width: itemWidth,
        },
      });
    }

    return {
      items,
      totalWidth,
    };
  }, [
    gap,
    itemCount,
    itemWidth,
    listState.scrollLeft,
    listState.width,
    overscanItems,
  ]);
};
