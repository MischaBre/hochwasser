<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";
import { Eye, EyeOff, X } from "lucide-vue-next";
import HydrographChart from "@/components/charts/HydrographChart.vue";
import StationsMap from "@/components/maps/StationsMap.vue";
import Button from "@/components/ui/button/Button.vue";
import BuyMeCoffeeButton from "@/components/BuyMeCoffeeButton.vue";
import Card from "@/components/ui/card/Card.vue";
import CardContent from "@/components/ui/card/CardContent.vue";
import CardHeader from "@/components/ui/card/CardHeader.vue";
import CardTitle from "@/components/ui/card/CardTitle.vue";
import Input from "@/components/ui/input/Input.vue";
import Label from "@/components/ui/label/Label.vue";
import Alert from "@/components/ui/alert/Alert.vue";
import { Waves, BellRing, ShieldCheck, Activity } from "lucide-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuth } from "@/composables/useAuth";
import {
  listPublicStationForecast,
  listPublicStationMeasurements,
  listPublicStations,
} from "@/features/stations/api";
import type { StationMeasurement, StationSummary } from "@/features/stations/types";
import { useFormatters } from "@/composables/useFormatters";
import {
  setAppLocale,
  supportedLocales,
  type SupportedLocale,
} from "@/plugins/i18n";
import { useAuthStore } from "@/stores/auth";

const { locale, t } = useI18n();
const { formatDateTime, formatNumber } = useFormatters();
const { isAuthenticated } = useAuth();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const cologneStationUuid = "a6ee8177-107b-47dd-bcfd-30960ccc6e9c";
type MappedStation = StationSummary & {
  latitude: number;
  longitude: number;
};

const email = ref("");
const password = ref("");
const passwordVisible = ref(false);
const errorMessage = ref("");
const selectedStationUuid = ref(cologneStationUuid);
const exampleLimitCm = ref<number>(560);

const showLoginModal = computed(() => route.name === "login");
const redirectPath = computed(() => (route.query.redirect as string) || "/app");

const localeModel = computed({
  get: () => locale.value,
  set: (value: string) => {
    if (supportedLocales.includes(value as SupportedLocale)) {
      setAppLocale(value as SupportedLocale);
    }
  },
});

const closeLoginModal = async () => {
  errorMessage.value = "";
  await router.push({ name: "landing" });
};

const submitLogin = async () => {
  errorMessage.value = "";

  try {
    await authStore.signIn(email.value.trim(), password.value);
    await router.push(redirectPath.value);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : t("auth.login.failedFallback");
    errorMessage.value = message;
  }
};

const openPrimaryCta = () => {
  router.push(isAuthenticated.value ? "/app" : "/register");
};

const stationsQuery = useQuery({
  queryKey: ["landing", "public-stations", "all"],
  queryFn: async () => {
    const all: StationSummary[] = [];
    const step = 200;
    let offset = 0;
    while (true) {
      const page = await listPublicStations({ limit: step, offset });
      all.push(...page.items);
      if (page.items.length < step) {
        break;
      }
      offset += step;
    }
    return all.filter(
      (station) =>
        typeof station.latitude === "number" && typeof station.longitude === "number",
    ) as MappedStation[];
  },
  staleTime: 10 * 60 * 1000,
});

const stations = computed<MappedStation[]>(() => stationsQuery.data.value ?? []);

const selectedStation = computed(() => {
  return (
    stations.value.find((station) => station.uuid === selectedStationUuid.value) ??
    stations.value[0] ??
    null
  );
});

const stationSeriesQuery = useQuery({
  queryKey: computed(() => [
    "landing",
    "station-series",
    selectedStation.value?.uuid || "",
  ]),
  queryFn: async () => {
    const stationUuid = selectedStation.value?.uuid || "";
    const [measurements, forecast] = await Promise.all([
      listPublicStationMeasurements(stationUuid, "P3D"),
      listPublicStationForecast(stationUuid),
    ]);
    return { measurements, forecast };
  },
  enabled: computed(() => Boolean(selectedStation.value?.uuid)),
  staleTime: 2 * 60 * 1000,
});

const pickRandomLimit = (
  measurements: StationMeasurement[],
  forecast: StationMeasurement[],
) => {
  const values = [...measurements, ...forecast].map((row) => row.value);
  if (values.length === 0) {
    exampleLimitCm.value = 560;
    return;
  }
  const min = Math.floor(Math.min(...values) - 20);
  const max = Math.ceil(Math.max(...values) + 20);
  const span = Math.max(1, max - min);
  const random = min + Math.floor(Math.random() * span);
  exampleLimitCm.value = random;
};

const rerollExampleLimit = () => {
  pickRandomLimit(
    stationSeriesQuery.data.value?.measurements ?? [],
    stationSeriesQuery.data.value?.forecast ?? [],
  );
};

watch(
  stations,
  (nextStations) => {
    if (nextStations.length === 0) {
      return;
    }
    if (!nextStations.some((station) => station.uuid === selectedStationUuid.value)) {
      const cologne = nextStations.find(
        (station) => station.uuid === cologneStationUuid,
      );
      selectedStationUuid.value = cologne?.uuid ?? nextStations[0].uuid;
    }
  },
  { immediate: true },
);

watch(
  () => stationSeriesQuery.data.value,
  (series) => {
    if (!series) {
      return;
    }
    pickRandomLimit(series.measurements, series.forecast);
  },
  { immediate: true },
);

const currentMeasurementValue = computed(() => {
  const measurements = stationSeriesQuery.data.value?.measurements ?? [];
  if (measurements.length === 0) {
    return null;
  }
  return measurements[measurements.length - 1].value;
});

const currentMeasurementTimestamp = computed(() => {
  const measurements = stationSeriesQuery.data.value?.measurements ?? [];
  if (measurements.length === 0) {
    return null;
  }
  return measurements[measurements.length - 1].timestamp;
});

const exampleState = computed(() => {
  const limit = exampleLimitCm.value;
  const current = currentMeasurementValue.value;
  const forecast = stationSeriesQuery.data.value?.forecast ?? [];
  const nowMs = Date.now();
  const futureForecast = forecast.filter((point) => {
    const ts = Date.parse(point.timestamp);
    return Number.isFinite(ts) && ts > nowMs;
  });

  if (current !== null && current >= limit) {
    const fallsBelow = futureForecast.some((point) => point.value < limit);
    return fallsBelow ? "crossing_soon_over" : "crossing_active";
  }

  const crossingIncoming = futureForecast.some((point) => point.value >= limit);
  return crossingIncoming ? "crossing_incoming" : "no_crossing";
});

const exampleStateLabel = computed(() => {
  return t(`landing.example.stateValues.${exampleState.value}`);
});

const exampleCrossingTimestamp = computed(() => {
  const forecast = stationSeriesQuery.data.value?.forecast ?? [];
  const crossing = forecast.find((point) => point.value >= exampleLimitCm.value);
  return crossing?.timestamp ?? currentMeasurementTimestamp.value ?? null;
});

const emailSubject = computed(() => {
  const stationName =
    selectedStation.value?.shortname || selectedStation.value?.longname || "-";
  return t("landing.example.email.subject", {
    station: stationName,
    limit: formatNumber(exampleLimitCm.value),
    unit: "cm",
  });
});

const emailIntro = computed(() => {
  return t(`landing.example.email.introValues.${exampleState.value}`);
});

const emailEventTime = computed(() => {
  if (!exampleCrossingTimestamp.value) {
    return t("jobDetails.fields.na");
  }
  return formatDateTime(exampleCrossingTimestamp.value);
});

const emailCurrentValue = computed(() => {
  if (currentMeasurementValue.value === null) {
    return t("jobDetails.fields.na");
  }
  return `${formatNumber(currentMeasurementValue.value)} cm`;
});

const emailCurrentTime = computed(() => {
  if (!currentMeasurementTimestamp.value) {
    return t("jobDetails.fields.na");
  }
  return formatDateTime(currentMeasurementTimestamp.value);
});

const exampleTriggerSource = computed(() => {
  if (currentMeasurementValue.value !== null && currentMeasurementValue.value >= exampleLimitCm.value) {
    return t("landing.example.email.triggerSourceCurrent");
  }
  return t("landing.example.email.triggerSourceOfficial");
});

const maxForecastPoint = computed(() => {
  const forecast = stationSeriesQuery.data.value?.forecast ?? [];
  if (forecast.length === 0) {
    return null;
  }
  return forecast.reduce((max, point) => (point.value > max.value ? point : max));
});

const emailMaxForecast = computed(() => {
  if (!maxForecastPoint.value) {
    return t("jobDetails.fields.na");
  }
  return `${formatNumber(maxForecastPoint.value.value)} cm`;
});

const emailMaxForecastTime = computed(() => {
  if (!maxForecastPoint.value) {
    return t("jobDetails.fields.na");
  }
  return formatDateTime(maxForecastPoint.value.timestamp);
});

const onSelectStation = (stationUuid: string) => {
  selectedStationUuid.value = stationUuid;
};
</script>

<template>
  <div class="landing-page">
    <div class="landing-shell">
      <header class="landing-header">
        <RouterLink class="landing-logo" to="/">
          <Waves class="h-5 w-5" />
          <span>Pegel-Alarm</span>
        </RouterLink>
        <div class="landing-actions">
          <label class="sr-only" for="landing-locale">{{
            t("shell.locale.label")
          }}</label>
          <select
            id="landing-locale"
            v-model="localeModel"
            class="h-8 rounded-md border border-input bg-background px-2 text-xs font-semibold uppercase tracking-wide"
          >
            <option
              v-for="nextLocale in supportedLocales"
              :key="nextLocale"
              :value="nextLocale"
            >
              {{ t(`shell.locale.${nextLocale}`) }}
            </option>
          </select>
          <RouterLink class="landing-link" to="/login">{{
            t("landing.actions.signIn")
          }}</RouterLink>
          <Button
            size="sm"
            class="landing-primary-btn"
            @click="openPrimaryCta"
            >{{
              isAuthenticated
                ? t("landing.actions.openDashboard")
                : t("landing.actions.createAccount")
            }}</Button
          >
        </div>
      </header>

      <main class="landing-main">
        <section class="hero">
          <p class="hero-kicker">{{ t("landing.kicker") }}</p>
          <h1 class="hero-title">{{ t("landing.title") }}</h1>
          <p class="hero-copy">{{ t("landing.copy") }}</p>
          <p class="hero-copy">{{ t("landing.freeParagraph") }}</p>

          <div class="hero-ctas">
            <Button @click="openPrimaryCta">{{
              isAuthenticated
                ? t("landing.actions.openDashboard")
                : t("landing.actions.startNow")
            }}</Button>
            <Button variant="outline" @click="router.push('/login')">{{
              t("landing.actions.signIn")
            }}</Button>
          </div>
        </section>

        <section class="feature-grid" aria-label="feature highlights">
          <article class="feature-card">
            <BellRing class="feature-icon" />
            <h2>{{ t("landing.features.alerting.title") }}</h2>
            <p>{{ t("landing.features.alerting.copy") }}</p>
          </article>
          <article class="feature-card">
            <Activity class="feature-icon" />
            <h2>{{ t("landing.features.monitoring.title") }}</h2>
            <p>{{ t("landing.features.monitoring.copy") }}</p>
          </article>
          <article class="feature-card">
            <ShieldCheck class="feature-icon" />
            <h2>{{ t("landing.features.sources.title") }}</h2>
            <p>{{ t("landing.features.sources.copy") }}</p>
          </article>
        </section>

        <section class="landing-example" aria-label="example station">
          <div class="example-header">
            <div>
              <p class="hero-kicker">{{ t("landing.example.kicker") }}</p>
              <h2 class="example-title">{{ t("landing.example.title") }}</h2>
              <p class="hero-copy">{{ t("landing.example.copy") }}</p>
            </div>
          </div>

          <div class="example-grid">
            <div class="example-column">
              <article class="example-chart-card">
                <p class="example-station-name">
                  {{ selectedStation?.longname || selectedStation?.shortname || t("landing.example.loading") }}
                </p>
                <HydrographChart
                  :measurements="stationSeriesQuery.data.value?.measurements ?? []"
                  :forecast="stationSeriesQuery.data.value?.forecast ?? []"
                  :limit="exampleLimitCm"
                />
                <div class="example-meta">
                  <p>
                    {{ t("landing.example.limitLabel") }}
                    <button
                      type="button"
                      class="example-limit-trigger"
                      @click="rerollExampleLimit"
                    >
                      {{ formatNumber(exampleLimitCm) }} cm
                    </button>
                  </p>
                  <p>
                    {{
                      t("landing.example.state", {
                        value: exampleStateLabel,
                      })
                    }}
                  </p>
                </div>
              </article>

              <article class="example-email" aria-label="example email">
                <p class="example-email-title">{{ t("landing.example.email.previewTitle") }}</p>
                <div class="example-email-frame">
                  <p><strong>{{ t("landing.example.email.fromLabel") }}</strong> alert{'@'}pegelalarm.de</p>
                  <p><strong>{{ t("landing.example.email.toLabel") }}</strong> max.mustermann{'@'}example.com</p>
                  <p>
                    <strong>{{ t("landing.example.email.subjectLabel") }}</strong>
                    {{ emailSubject }}
                  </p>
                  <hr class="example-email-divider" />
                  <p class="example-email-section">{{ t("landing.example.email.sectionStationInformation") }}</p>
                  <p>
                    {{ t("landing.example.email.stationNumberLine", { value: selectedStation?.number || t("jobDetails.fields.na") }) }}
                  </p>
                  <p>
                    {{ t("landing.example.email.longNameLine", { value: selectedStation?.longname || selectedStation?.shortname || t("jobDetails.fields.na") }) }}
                  </p>
                  <p>
                    {{ t("landing.example.email.waterBodyLine", { value: selectedStation?.water_longname || selectedStation?.water_shortname || t("jobDetails.fields.na") }) }}
                  </p>
                  <p class="example-email-section">{{ t("landing.example.email.sectionAlertContext") }}</p>
                  <p>{{ emailIntro }}</p>
                  <p>
                    {{ t("landing.example.email.thresholdLine", { value: formatNumber(exampleLimitCm) }) }}
                  </p>
                  <p>
                    {{ t("landing.example.email.currentValueLine", { value: emailCurrentValue, time: emailCurrentTime }) }}
                  </p>
                  <p>
                    {{ t("landing.example.email.triggerSourceLine", { value: exampleTriggerSource }) }}
                  </p>
                  <p>
                    {{ t("landing.example.email.triggerTimeLine", { value: emailEventTime }) }}
                  </p>
                  <p>
                    {{ t("landing.example.email.maxForecastLine", { value: emailMaxForecast, time: emailMaxForecastTime }) }}
                  </p>
                </div>
              </article>
            </div>

            <article class="example-map-card">
              <p class="example-station-name">
                {{
                  t("landing.example.stationCount", {
                    value: formatNumber(stations.length),
                  })
                }}
              </p>
              <StationsMap
                :stations="stations"
                :selected-uuid="selectedStationUuid"
                @select="onSelectStation"
              />
              <p class="example-map-copy">
                {{ t("landing.example.mapHint") }}
              </p>
            </article>
          </div>
        </section>

        <section class="steps-grid" aria-label="how it works">
          <article class="step-card">
            <p class="step-number">1</p>
            <h2>{{ t("landing.steps.pickStation.title") }}</h2>
            <p>{{ t("landing.steps.pickStation.copy") }}</p>
          </article>
          <article class="step-card">
            <p class="step-number">2</p>
            <h2>{{ t("landing.steps.setLimit.title") }}</h2>
            <p>{{ t("landing.steps.setLimit.copy") }}</p>
          </article>
          <article class="step-card">
            <p class="step-number">3</p>
            <h2>{{ t("landing.steps.getAlert.title") }}</h2>
            <p>{{ t("landing.steps.getAlert.copy") }}</p>
          </article>
        </section>
      </main>

      <footer class="landing-footer">
        <p>{{ t("landing.footer.source") }}</p>
        <p class="landing-donate-copy">{{ t("landing.footer.donate") }}</p>
        <div class="landing-footer-links">
          <a href="https://pegelonline.wsv.de" target="_blank" rel="noreferrer"
            >Pegelonline</a
          >
          <RouterLink to="/impressum">{{
            t("landing.actions.imprint")
          }}</RouterLink>
          <RouterLink to="/datenschutz">{{
            t("landing.actions.privacy")
          }}</RouterLink>
          <BuyMeCoffeeButton />
        </div>
      </footer>
    </div>

    <div
      v-if="showLoginModal"
      class="login-modal-backdrop"
      role="dialog"
      aria-modal="true"
      :aria-label="t('auth.login.title')"
    >
      <Card class="login-modal-card">
        <CardHeader>
          <div class="login-modal-headline">
            <CardTitle>{{ t("auth.login.title") }}</CardTitle>
            <button
              type="button"
              class="login-modal-close"
              :aria-label="t('auth.login.close')"
              @click="closeLoginModal"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <form class="space-y-3" @submit.prevent="submitLogin">
            <div class="space-y-2">
              <Label for="login-email">{{ t("auth.login.email") }}</Label>
              <Input
                id="login-email"
                v-model="email"
                autocomplete="email"
                type="email"
                required
              />
            </div>

            <div class="space-y-2">
              <Label for="login-password">{{ t("auth.login.password") }}</Label>
              <div class="relative">
                <Input
                  id="login-password"
                  v-model="password"
                  autocomplete="current-password"
                  :type="passwordVisible ? 'text' : 'password'"
                  class="pr-11"
                  required
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 inline-flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
                  :aria-label="
                    passwordVisible
                      ? t('auth.login.hidePassword')
                      : t('auth.login.showPassword')
                  "
                  @click="passwordVisible = !passwordVisible"
                >
                  <EyeOff v-if="passwordVisible" class="h-4 w-4" />
                  <Eye v-else class="h-4 w-4" />
                </button>
              </div>
            </div>

            <Alert v-if="errorMessage" variant="destructive">{{
              errorMessage
            }}</Alert>

            <div class="flex flex-wrap justify-end gap-2 pt-1">
              <Button
                type="button"
                variant="outline"
                @click="closeLoginModal"
                >{{ t("auth.login.cancel") }}</Button
              >
              <Button type="submit" :disabled="authStore.loading">
                {{
                  authStore.loading
                    ? t("auth.login.submitting")
                    : t("auth.login.submit")
                }}
              </Button>
            </div>

            <p class="text-sm text-muted-foreground">
              {{ t("auth.login.newHere") }}
              <RouterLink
                class="font-semibold text-primary hover:underline"
                to="/register"
                >{{ t("auth.login.createAccount") }}</RouterLink
              >
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.landing-page {
  min-height: 100vh;
  padding: 1.25rem;
}

.landing-shell {
  margin: 0 auto;
  display: flex;
  min-height: calc(100vh - 2.5rem);
  max-width: 72rem;
  flex-direction: column;
  gap: 2rem;
  border: 1px solid hsl(var(--border));
  border-radius: 1.25rem;
  background: linear-gradient(
    160deg,
    hsl(var(--card)) 0%,
    hsl(var(--muted) / 0.45) 100%
  );
  padding: 1.25rem;
}

.landing-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.landing-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: hsl(var(--foreground));
  text-decoration: none;
}

.landing-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  width: 100%;
}

.landing-actions select {
  min-width: 4.2rem;
}

.landing-primary-btn {
  margin-left: auto;
}

.landing-link {
  font-size: 0.875rem;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  text-decoration: none;
}

.landing-link:hover {
  color: hsl(var(--foreground));
}

.landing-main {
  display: grid;
  gap: 1.75rem;
}

.hero {
  border-radius: 1rem;
  border: 1px solid hsl(var(--border));
  background: radial-gradient(
      circle at 80% 0%,
      hsl(var(--accent) / 0.5),
      transparent 45%
    ),
    linear-gradient(180deg, hsl(var(--card)) 0%, hsl(var(--muted) / 0.2) 100%);
  padding: 2rem 1.5rem;
}

.hero-kicker {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
}

.hero-title {
  margin: 0.75rem 0 0;
  max-width: 28.8ch;
  font-size: clamp(1.9rem, 5vw, 3rem);
  line-height: 1.1;
}

.hero-copy {
  margin: 1rem 0 0;
  max-width: 64.8ch;
  font-size: 1rem;
  color: hsl(var(--muted-foreground));
  line-height: 1.6;
}

.hero-ctas {
  margin-top: 1.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.landing-example {
  border: 1px solid hsl(var(--border));
  border-radius: 1rem;
  background: linear-gradient(
    160deg,
    hsl(var(--card)) 0%,
    hsl(var(--muted) / 0.2) 100%
  );
  padding: 1rem;
  display: grid;
  gap: 1rem;
}

.example-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 0.75rem;
}

.example-title {
  margin: 0.25rem 0 0;
  font-size: clamp(1.25rem, 2.3vw, 1.75rem);
}

.example-grid {
  display: grid;
  gap: 0.95rem;
}

.example-column {
  display: grid;
  gap: 0.95rem;
  align-content: start;
}

.example-chart-card,
.example-map-card {
  border: 1px solid hsl(var(--border));
  border-radius: 0.9rem;
  background: hsl(var(--card));
  padding: 0.9rem;
  display: grid;
  gap: 0.75rem;
}

.example-station-name {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
}

.example-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  font-size: 0.85rem;
  color: hsl(var(--muted-foreground));
}

.example-meta p,
.example-map-copy {
  margin: 0;
}

.example-limit-trigger {
  border: 0;
  background: transparent;
  padding: 0;
  margin: 0;
  color: hsl(var(--foreground));
  font-weight: 700;
  cursor: pointer;
}

.example-limit-trigger:hover {
  text-decoration: underline;
}

.example-map-copy {
  font-size: 0.84rem;
  color: hsl(var(--muted-foreground));
}

.example-email {
  margin-top: 0.3rem;
  border: 1px solid hsl(var(--border));
  border-radius: 0.85rem;
  background: hsl(var(--background));
  overflow: hidden;
}

.example-email-title {
  margin: 0;
  padding: 0.55rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
  background: hsl(var(--muted) / 0.4);
}

.example-email-frame {
  display: grid;
  gap: 0.45rem;
  padding: 0.8rem;
  font-size: 0.84rem;
  line-height: 1.45;
  color: hsl(var(--foreground));
}

.example-email-frame p {
  margin: 0;
}

.example-email-section {
  margin-top: 0.25rem;
  font-size: 0.77rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
}

.example-email-divider {
  border: 0;
  border-top: 1px solid hsl(var(--border));
  margin: 0.1rem 0 0.2rem;
}

.feature-grid {
  display: grid;
  gap: 0.85rem;
}

.steps-grid {
  display: grid;
  gap: 0.85rem;
}

.feature-card {
  border: 1px solid hsl(var(--border));
  border-radius: 0.9rem;
  padding: 1rem;
  background: hsl(var(--card));
}

.feature-card h2 {
  margin: 0.65rem 0 0;
  font-size: 1rem;
}

.feature-card p {
  margin: 0.5rem 0 0;
  font-size: 0.92rem;
  color: hsl(var(--muted-foreground));
  line-height: 1.5;
}

.step-card {
  border: 1px solid hsl(var(--border));
  border-radius: 0.9rem;
  padding: 1rem;
  background: hsl(var(--card));
}

.step-number {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
}

.step-card h2 {
  margin: 0.55rem 0 0;
  font-size: 1rem;
}

.step-card p {
  margin: 0.5rem 0 0;
  font-size: 0.92rem;
  color: hsl(var(--muted-foreground));
  line-height: 1.5;
}

.feature-icon {
  height: 1.1rem;
  width: 1.1rem;
  color: hsl(var(--primary));
}

.landing-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  border-top: 1px solid hsl(var(--border));
  padding-top: 1rem;
  font-size: 0.82rem;
  color: hsl(var(--muted-foreground));
}

.landing-footer p {
  margin: 0;
}

.landing-donate-copy {
  color: hsl(var(--foreground));
}

.landing-footer-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
}

.landing-footer-links a {
  color: hsl(var(--foreground));
  font-weight: 600;
  text-decoration: none;
}

.landing-footer-links :deep(.buy-me-coffee-slot) {
  min-height: 40px;
}

.landing-footer-links :deep(.bmc-button) {
  font-size: 0.75rem;
  padding: 0.42rem 0.62rem;
}

.landing-footer-links a:hover {
  text-decoration: underline;
}

.login-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(204 29% 13% / 0.5);
  backdrop-filter: blur(2px);
  padding: 1rem;
}

.login-modal-card {
  width: 100%;
  max-width: 26rem;
  max-height: calc(100dvh - 1.5rem);
  overflow: auto;
}

.login-modal-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.login-modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 999px;
  border: 1px solid hsl(var(--border));
  background: hsl(var(--background));
  color: hsl(var(--muted-foreground));
}

.login-modal-close:hover {
  color: hsl(var(--foreground));
}

@media (min-width: 768px) {
  .landing-page {
    padding: 1.75rem;
  }

  .landing-shell {
    min-height: calc(100vh - 3.5rem);
    padding: 1.5rem;
  }

  .feature-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .example-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
  }

  .steps-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .landing-header {
    align-items: center;
    flex-wrap: nowrap;
  }

  .landing-actions {
    width: auto;
  }

  .landing-primary-btn {
    margin-left: 0;
  }
}
</style>
