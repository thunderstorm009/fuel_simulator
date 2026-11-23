import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

export type StreamStatus = "live" | "fallback";

export function useEventStream(): { status: StreamStatus } {
  const [status, setStatus] = useState<StreamStatus>("fallback");
  const queryClient = useQueryClient();

  useEffect(() => {
    if (typeof EventSource === "undefined") {
      setStatus("fallback");
      return;
    }

    let eventSource: EventSource | null = null;
    let isMounted = true;

    try {
      eventSource = new EventSource("/api/stream");

      eventSource.onopen = () => {
        if (isMounted) {
          setStatus("live");
        }
      };

      eventSource.onerror = () => {
        if (isMounted) {
          setStatus("fallback");
        }
      };

      eventSource.addEventListener("snapshot", () => {
        queryClient.invalidateQueries({ queryKey: ["state"] });
        queryClient.invalidateQueries({ queryKey: ["events"] });
        queryClient.invalidateQueries({ queryKey: ["risks"] });
        queryClient.invalidateQueries({ queryKey: ["depotRisks"] });
      });

      eventSource.addEventListener("forecasts", () => {
        queryClient.invalidateQueries({ queryKey: ["risks"] });
        queryClient.invalidateQueries({ queryKey: ["trajectory"] });
      });

      eventSource.addEventListener("recommendations", () => {
        queryClient.invalidateQueries({ queryKey: ["recommendations"] });
        queryClient.invalidateQueries({ queryKey: ["decisions"] });
      });

      eventSource.addEventListener("incidents", () => {
        queryClient.invalidateQueries({ queryKey: ["incidents"] });
        queryClient.invalidateQueries({ queryKey: ["events"] });
        queryClient.invalidateQueries({ queryKey: ["alerts"] });
      });
    } catch {
      if (isMounted) {
        setStatus("fallback");
      }
    }

    return () => {
      isMounted = false;
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [queryClient]);

  return { status };
}
