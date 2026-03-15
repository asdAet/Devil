import type { ComponentPropsWithoutRef, ElementType, ReactNode } from "react";

import styles from "../../styles/ui/Card.module.css";

type CardProps<T extends ElementType = "section"> = {
  as?: T;
  wide?: boolean;
  className?: string;
  children: ReactNode;
} & Omit<ComponentPropsWithoutRef<T>, "as" | "className" | "children">;

/**
 * Универсальный контейнер карточки.
 * @param props Настройки контейнера и вложенное содержимое.
 * @returns JSX-контейнер с карточным оформлением.
 */
export function Card<T extends ElementType = "section">({
  as,
  wide = false,
  className,
  children,
  ...rest
}: CardProps<T>) {
  const Component = as ?? "section";
  return (
    <Component
      {...rest}
      className={[styles.card, wide ? styles.wide : "", className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </Component>
  );
}
