import { AgentHero } from "./looks/agent-hero";
import { DropHero } from "./looks/drop-hero";
import { RenaissanceHero } from "./looks/renaissance-hero";

/**
 * Every look's hero is in the page; CSS shows the active one before first
 * paint (see .look-* in globals.css), so switching looks never reloads and
 * nobody sees the wrong hero flash. Heavy WebGL only loads for the active one.
 */
function HomeHero() {
  return (
    <>
      <div className="look-renaissance">
        <RenaissanceHero />
      </div>
      <div className="look-agent">
        <AgentHero />
      </div>
      <div className="look-drop">
        <DropHero />
      </div>
    </>
  );
}

export { HomeHero };
