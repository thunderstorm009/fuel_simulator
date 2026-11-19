import type { Incident, SimulatorEvent } from "../../types/api";
import { localTime } from "../../lib/format";
import StatusPill from "../../components/ui/StatusPill";

export default function EventsPanel({ events, incidents }: { events: SimulatorEvent[]; incidents: Incident[] }) {
  return (
    <section className="panel section-panel">
      <div className="section-heading"><div><p className="eyebrow">LIVE CONDITIONS</p><h2>Events & incidents</h2></div><span className="count-badge">{events.length + incidents.length}</span></div>
      <div className="event-list">
        {events.map((event) => (
          <article className="event-row" key={`event-${event.id}`}>
            <span className="event-marker" />
            <div><strong>{event.type.replaceAll("_", " ")}</strong><p>Ticks {event.start_tick}–{event.end_tick}</p></div>
            <StatusPill status={event.status} />
          </article>
        ))}
        {incidents.map((incident) => (
          <article className="event-row" key={`incident-${incident.id}`}>
            <span className="event-marker incident-marker" />
            <div><strong>{incident.type.replaceAll("_", " ")}</strong><p>{incident.detected_at ? localTime(incident.detected_at) : "Platform incident"}</p></div>
            <StatusPill status={incident.severity} />
          </article>
        ))}
        {events.length === 0 && incidents.length === 0 && <p className="empty-note">No active simulator events or platform incidents.</p>}
      </div>
    </section>
  );
}
