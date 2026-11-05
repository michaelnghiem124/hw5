/**
 * A split-flap ("Solari") display for the checking balance.
 *
 * Real airport boards cannot jump straight to a character: each flap rotates through
 * the intervening ones. That mechanical constraint is the whole effect, so this
 * reproduces it rather than cross-fading -- each digit steps through the characters
 * between its old and new value, and digits that did not change do not move at all.
 *
 * It earns its place on a money dashboard: a balance that silently rewrites itself is
 * easy to miss, and the one number on this board that must never change unnoticed is
 * the cash. The flapping draws the eye to exactly the digits that moved.
 */

import { useEffect, useRef, useState } from "react";
import "./SplitFlap.css";

const GLYPHS = "0123456789,.$ ";
const STEP_MS = 55;

function Flap({ target, delay }: { target: string; delay: number }) {
  const [shown, setShown] = useState(target);
  const [flipping, setFlipping] = useState(false);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    if (shown === target) return;

    const from = GLYPHS.indexOf(shown);
    const to = GLYPHS.indexOf(target);
    // A glyph outside the set (shouldn't happen) snaps rather than spinning forever.
    if (from < 0 || to < 0) {
      setShown(target);
      return;
    }

    // Always travel forwards through the strip, wrapping -- that is the direction a
    // real flap can physically turn.
    const distance = (to - from + GLYPHS.length) % GLYPHS.length;
    setFlipping(true);

    for (let step = 1; step <= distance; step++) {
      timers.current.push(
        window.setTimeout(
          () => {
            setShown(GLYPHS[(from + step) % GLYPHS.length]);
            if (step === distance) setFlipping(false);
          },
          delay + step * STEP_MS,
        ),
      );
    }

    return () => {
      timers.current.forEach(clearTimeout);
      timers.current = [];
    };
    // `shown` is deliberately excluded: it changes on every step of the animation and
    // including it would restart the sequence from each intermediate glyph.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, delay]);

  const isSeparator = shown === "," || shown === "." || shown === " ";

  return (
    <span
      className={
        "flap" +
        (flipping ? " flap--turning" : "") +
        (isSeparator ? " flap--thin" : "")
      }
      aria-hidden="true"
    >
      <span className="flap__glyph">{shown}</span>
      <span className="flap__seam" />
    </span>
  );
}

export function SplitFlap({
  value,
  label,
  tone = "normal",
}: {
  value: number;
  label: string;
  tone?: "normal" | "warn" | "danger";
}) {
  // Right-aligned into a fixed width so the digits sit still as the number shrinks --
  // a board whose columns shuffle sideways is unreadable at a glance.
  const text = `$${value.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`.padStart(9, " ");

  return (
    <div className={`splitflap splitflap--${tone}`}>
      <div className="splitflap__label eyebrow">{label}</div>
      <div
        className="splitflap__row"
        role="status"
        aria-live="polite"
        aria-label={`${label}: ${text.trim()}`}
      >
        {text.split("").map((char, i) => (
          <Flap key={i} target={char} delay={i * 28} />
        ))}
      </div>
    </div>
  );
}
