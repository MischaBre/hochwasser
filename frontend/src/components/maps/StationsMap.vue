<script setup lang="ts">
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { StationSummary } from "@/features/stations/types";

type StationPoint = StationSummary & {
  latitude: number;
  longitude: number;
};

const props = defineProps<{
  stations: StationPoint[];
  selectedUuid: string;
  ariaLabel?: string;
}>();

const emit = defineEmits<{
  (e: "select", stationUuid: string): void;
}>();

const mapContainer = ref<HTMLDivElement | null>(null);
let map: L.Map | null = null;
let markersLayer: L.LayerGroup | null = null;
const markerByUuid = new Map<string, L.CircleMarker>();
let didFitBounds = false;
let destroyed = false;

const tokenColor = (token: string, alpha?: number): string => {
  if (typeof document === "undefined") {
    return `hsl(0 0% 45%${typeof alpha === "number" ? ` / ${alpha}` : ""})`;
  }

  const tokenValue = getComputedStyle(document.documentElement)
    .getPropertyValue(token)
    .trim();
  if (!tokenValue) {
    return `hsl(0 0% 45%${typeof alpha === "number" ? ` / ${alpha}` : ""})`;
  }

  return `hsl(${tokenValue}${typeof alpha === "number" ? ` / ${alpha}` : ""})`;
};

const defaultMarkerStyle: L.CircleMarkerOptions = {
  radius: 5,
  color: tokenColor("--primary", 0.9),
  weight: 1.5,
  fillColor: tokenColor("--primary", 0.75),
  fillOpacity: 0.64,
};

const selectedMarkerStyle: L.CircleMarkerOptions = {
  radius: 7,
  color: tokenColor("--destructive", 0.94),
  weight: 2,
  fillColor: tokenColor("--destructive", 0.88),
  fillOpacity: 0.9,
};

const ensureMap = () => {
  if (!mapContainer.value || map || destroyed) {
    return;
  }

  map = L.map(mapContainer.value, {
    center: [51.2, 10.4],
    zoom: 5,
    zoomControl: true,
    minZoom: 4,
    maxZoom: 12,
    zoomSnap: 1,
    preferCanvas: true,
    maxBounds: L.latLngBounds([47.0, 5.0], [55.8, 15.8]),
    maxBoundsViscosity: 0.8,
    worldCopyJump: false,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    noWrap: true,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors',
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
};

const stationLabel = (station: StationPoint): string => {
  const water = station.water_longname || station.water_shortname;
  return water ? `${station.shortname} (${water})` : station.shortname;
};

const redrawMarkers = () => {
  if (!map || !markersLayer || destroyed) {
    return;
  }

  markersLayer.clearLayers();
  markerByUuid.clear();

  const latLngs: L.LatLngExpression[] = [];

  for (const station of props.stations) {
    const latLng: L.LatLngTuple = [station.latitude, station.longitude];
    latLngs.push(latLng);
    const marker = L.circleMarker(latLng, defaultMarkerStyle)
      .bindPopup(stationLabel(station))
      .on("click", () => {
        emit("select", station.uuid);
      });

    marker.addTo(markersLayer);
    markerByUuid.set(station.uuid, marker);
  }

  applySelectionStyle();

  if (!didFitBounds && latLngs.length > 0) {
    map.fitBounds(L.latLngBounds(latLngs), { padding: [28, 28] });
    didFitBounds = true;
  }
};

const applySelectionStyle = () => {
  if (!map || destroyed) {
    return;
  }

  for (const [uuid, marker] of markerByUuid.entries()) {
    marker.setStyle(uuid === props.selectedUuid ? selectedMarkerStyle : defaultMarkerStyle);
  }

  if (props.selectedUuid) {
    const selected = markerByUuid.get(props.selectedUuid);
    if (selected) {
      map?.panTo(selected.getLatLng(), { animate: true, duration: 0.35 });
    }
  }
};

onMounted(() => {
  destroyed = false;
  ensureMap();
  void nextTick(() => {
    if (!map || destroyed) {
      return;
    }
    map.invalidateSize(false);
    redrawMarkers();
  });
});

watch(
  () => props.stations,
  () => {
    if (destroyed) {
      return;
    }
    ensureMap();
    redrawMarkers();
  },
  { deep: true, flush: "post" },
);

watch(
  () => props.selectedUuid,
  () => {
    if (destroyed) {
      return;
    }
    applySelectionStyle();
  },
  { flush: "post" },
);

onBeforeUnmount(() => {
  destroyed = true;
  markerByUuid.clear();
  markersLayer?.clearLayers();
  markersLayer = null;
  map?.remove();
  map = null;
});
</script>

<template>
  <div class="stations-map-shell">
    <div
      ref="mapContainer"
      class="stations-map"
      role="img"
      :aria-label="props.ariaLabel || 'Interactive gauge station map'"
    />
  </div>
</template>

<style scoped>
.stations-map-shell {
  width: 100%;
  border: 1px solid hsl(var(--border));
  border-radius: 1rem;
  overflow: hidden;
  background: hsl(var(--card));
  box-shadow: inset 0 0 0 1px hsl(var(--background) / 0.5);
}

.stations-map {
  width: 100%;
  height: 420px;
}

@media (max-width: 767px) {
  .stations-map {
    height: 320px;
  }
}

.stations-map-shell :deep(.leaflet-control-zoom) {
  border: 1px solid hsl(var(--border));
  border-radius: 0.7rem;
  overflow: hidden;
}

.stations-map-shell :deep(.leaflet-control-zoom a) {
  background: hsl(var(--card));
  color: hsl(var(--foreground));
}

.stations-map-shell :deep(.leaflet-popup-content-wrapper) {
  border-radius: 0.7rem;
}

.stations-map-shell :deep(.leaflet-popup-content) {
  margin: 0.65rem 0.75rem;
  max-width: 220px;
  font-size: 0.86rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.stations-map-shell :deep(.leaflet-control-attribution) {
  background: hsl(var(--background) / 0.82);
  color: hsl(var(--muted-foreground));
  backdrop-filter: blur(2px);
}
</style>
