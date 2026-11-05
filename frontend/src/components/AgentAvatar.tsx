/**
 * A little portrait for each agent, drawn rather than labelled.
 *
 * Two-tone on purpose, and the rule is mechanical: the disc is the agent's colour, the
 * figure is cut out of it in the page's darkest navy, and anything sitting *on* the
 * figure is drawn back in the agent's colour. That keeps every persona legible against
 * five very different background colours -- a flat illustration in fixed colours would
 * disappear on the yellow Boss or glare on the violet Customer Service.
 *
 * Each one carries the prop that says what it does, so the floor reads without a legend:
 * the Boss wears the crown, Inventory carries the box, Accounting has the glasses and the
 * bow tie, Facilities the hard hat and hi-vis straps, Customer Service the headset. They
 * are deliberately a bit silly. A back-office staffed by five identical grey circles is
 * harder to read and no more serious.
 */

import { useId } from "react";
import type { ReactNode } from "react";
import type { AgentRole } from "../types";
import "./AgentAvatar.css";

/** Head, neck and shoulders. Every persona is built on this. */
function Figure() {
  return (
    <>
      <rect className="ink" x="16.6" y="21" width="6.8" height="9" />
      <path className="ink" d="M4 42c0-8.2 7.2-13.2 16-13.2S36 33.8 36 42Z" />
      <circle className="ink" cx="20" cy="17" r="7" />
    </>
  );
}

function Face({ smile = true }: { smile?: boolean }) {
  return (
    <>
      <circle className="lite" cx="17.3" cy="16.3" r="1.15" />
      <circle className="lite" cx="22.7" cy="16.3" r="1.15" />
      {smile && (
        <path className="stroke-lite" strokeWidth="1.3" d="M17.5 20.1q2.5 2 5 0" />
      )}
    </>
  );
}

const PERSONA: Record<AgentRole, ReactNode> = {
  // The Boss: crown, collar, tie. The crown sits above the head on open disc, so it is
  // drawn in ink -- the one prop that is not cut back out in the agent colour.
  boss: (
    <>
      <path className="ink" d="M12.6 10.8V5.9l3.3 2.5L20 3.4l4.1 5 3.3-2.5v4.9Z" />
      <Figure />
      <Face />
      <path
        className="lite"
        d="M20 30.4l-4.7-2-1.6 4.2 6.3 2.7 6.3-2.7-1.6-4.2Z"
      />
      <path className="ink" d="M20 31.3l-1.9 1.5 1.9 7.2 1.9-7.2Z" />
    </>
  ),

  // Inventory: a taped box, held up front.
  inventory: (
    <>
      <Figure />
      <path className="lite" d="M13.4 13.4a6.8 6.8 0 0 1 13.2 0Z" />
      <rect className="ink" x="11.8" y="12.7" width="16.4" height="2.6" rx="1.3" />
      <Face />
      <rect className="lite" x="11.6" y="29.4" width="16.8" height="11" rx="1" />
      <rect className="ink" x="19.2" y="29.4" width="1.6" height="11" />
      <rect className="ink" x="11.6" y="33.6" width="16.8" height="1.6" />
    </>
  ),

  // Accounting: round glasses and a bow tie.
  accounting: (
    <>
      <Figure />
      <Face smile={false} />
      <circle className="stroke-lite" strokeWidth="1.1" cx="16.9" cy="16.5" r="2.4" />
      <circle className="stroke-lite" strokeWidth="1.1" cx="23.1" cy="16.5" r="2.4" />
      <path className="stroke-lite" strokeWidth="1.1" d="M19.3 16.5h1.4" />
      <path className="stroke-lite" strokeWidth="1.3" d="M17.6 20.5h4.8" />
      <path className="lite" d="M20 31.2l-4.6-2.4v5ZM20 31.2l4.6-2.4v5Z" />
      <circle className="lite" cx="20" cy="31.2" r="1.6" />
      <circle className="ink" cx="20" cy="31.2" r="0.7" />
    </>
  ),

  // Facilities: hard hat and hi-vis straps.
  facilities: (
    <>
      <Figure />
      <path className="lite" d="M13.2 13.2a6.8 6.8 0 0 1 13.6 0Z" />
      <rect className="lite" x="10.4" y="12.4" width="19.2" height="2.8" rx="1.4" />
      <path className="stroke-ink" strokeWidth="1.1" d="M20 7.4v5" />
      <Face />
      <path className="stroke-lite" strokeWidth="2" d="M16.4 29.8 18.6 41" />
      <path className="stroke-lite" strokeWidth="2" d="M23.6 29.8 21.4 41" />
    </>
  ),

  // Customer Service: headset, boom mic, the widest smile on the floor.
  customer_service: (
    <>
      <Figure />
      <path className="stroke-lite" strokeWidth="2.2" d="M11.8 18a8.2 8.2 0 0 1 16.4 0" />
      <rect className="lite" x="9.8" y="16.2" width="3.4" height="5.8" rx="1.7" />
      <rect className="lite" x="26.8" y="16.2" width="3.4" height="5.8" rx="1.7" />
      <Face smile={false} />
      <path className="stroke-lite" strokeWidth="1.4" d="M17 20q3 2.8 6 0" />
      <path className="stroke-lite" strokeWidth="1.4" d="M11.5 22q.4 3.4 4.6 3.6" />
      <circle className="lite" cx="16.4" cy="25.6" r="1.2" />
    </>
  ),
};

export function AgentAvatar({ role, size = 34 }: { role: AgentRole; size?: number }) {
  // useId contains colons, which break a url(#...) reference.
  const clip = `cut-${useId().replace(/:/g, "")}`;

  return (
    <svg
      className="avatar"
      viewBox="0 0 40 40"
      width={size}
      height={size}
      role="img"
      aria-hidden="true"
    >
      <defs>
        <clipPath id={clip}>
          <circle cx="20" cy="20" r="20" />
        </clipPath>
      </defs>
      <g clipPath={`url(#${clip})`}>
        <circle cx="20" cy="20" r="20" fill="currentColor" />
        {PERSONA[role]}
      </g>
    </svg>
  );
}
