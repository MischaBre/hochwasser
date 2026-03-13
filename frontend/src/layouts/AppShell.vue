<script setup lang="ts">
import BuyMeCoffeeButton from "@/components/BuyMeCoffeeButton.vue";
import Button from "@/components/ui/button/Button.vue";
import { computed } from "vue";
import { RouterLink, RouterView } from "vue-router";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import { useAuth } from "@/composables/useAuth";
import {
  setAppLocale,
  supportedLocales,
  type SupportedLocale,
} from "@/plugins/i18n";

const { isAuthenticated, userEmail, signOut } = useAuth();
const route = useRoute();
const { locale, t } = useI18n();

const overviewActive = computed(() => route.path === "/app");
const jobsActive = computed(() => route.path.startsWith("/app/jobs"));
const accountActive = computed(() => route.path.startsWith("/app/account"));

const localeModel = computed({
  get: () => locale.value,
  set: (value: string) => {
    if (supportedLocales.includes(value as SupportedLocale)) {
      setAppLocale(value as SupportedLocale);
    }
  },
});

const navClass = (active: boolean): string => {
  return active
    ? "rounded-md border border-primary/30 bg-primary/15 px-3 py-2 text-sm font-semibold text-foreground shadow-[0_6px_16px_hsl(var(--primary)/0.18)]"
    : "rounded-md border border-transparent px-3 py-2 text-sm font-semibold text-muted-foreground hover:border-primary/20 hover:bg-primary/10 hover:text-foreground";
};
</script>

<template>
  <div class="app-shell-wrap">
    <div
      class="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-6 md:px-8"
    >
      <header
        class="mb-6 flex flex-col gap-3 rounded-xl border border-primary/20 bg-card/90 px-4 py-4 shadow-[0_14px_32px_hsl(var(--primary)/0.12)] backdrop-blur sm:px-5 md:flex-row md:items-center md:justify-between"
      >
        <div
          class="flex w-full items-start justify-between gap-3 md:w-auto md:items-center md:justify-start md:gap-5"
        >
          <div>
            <p
              class="text-xs font-extrabold uppercase tracking-[0.13em] text-primary"
            >
              {{ t("shell.appName") }}
            </p>
            <h1 class="text-2xl font-semibold md:text-3xl">
              {{ t("shell.appSection") }}
            </h1>
          </div>
          <nav class="hidden items-center gap-2 md:flex">
            <RouterLink :class="navClass(overviewActive)" to="/app">{{
              t("shell.nav.overview")
            }}</RouterLink>
            <RouterLink :class="navClass(jobsActive)" to="/app/jobs">{{
              t("shell.nav.jobs")
            }}</RouterLink>
            <RouterLink :class="navClass(accountActive)" to="/app/account">{{
              t("shell.nav.account")
            }}</RouterLink>
          </nav>
        </div>
        <div
          class="flex w-full flex-wrap items-center gap-2 md:w-auto md:gap-3"
        >
          <label class="sr-only" for="app-locale">{{
            t("shell.locale.label")
          }}</label>
          <select
            id="app-locale"
            v-model="localeModel"
            class="h-8 rounded-md border border-input bg-background px-2 text-xs font-semibold uppercase tracking-wide shadow-[inset_0_1px_0_hsl(var(--foreground)/0.06)]"
          >
            <option
              v-for="nextLocale in supportedLocales"
              :key="nextLocale"
              :value="nextLocale"
            >
              {{ t(`shell.locale.${nextLocale}`) }}
            </option>
          </select>
          <p
            v-if="isAuthenticated"
            class="hidden text-sm text-muted-foreground lg:block"
          >
            {{ userEmail }}
          </p>
          <Button
            v-if="isAuthenticated"
            variant="outline"
            size="sm"
            @click="signOut"
          >
            {{ t("shell.actions.signOut") }}
          </Button>
        </div>
      </header>

      <nav class="mb-4 flex items-center gap-2 md:hidden">
        <RouterLink :class="navClass(overviewActive)" to="/app">{{
          t("shell.nav.overview")
        }}</RouterLink>
        <RouterLink :class="navClass(jobsActive)" to="/app/jobs">{{
          t("shell.nav.jobs")
        }}</RouterLink>
        <RouterLink :class="navClass(accountActive)" to="/app/account">{{
          t("shell.nav.account")
        }}</RouterLink>
      </nav>

      <main class="pb-6">
        <RouterView />
      </main>

      <footer class="landing-footer">
        <p>{{ t("landing.footer.source") }}</p>
        <p class="landing-donate-copy">{{ t("landing.footer.donate") }}</p>
        <div class="landing-footer-links">
          <a href="https://pegelonline.wsv.de" target="_blank" rel="noreferrer"
            >Pegelonline</a
          >
          <RouterLink to="/impressum">{{ t("landing.actions.imprint") }}</RouterLink>
          <RouterLink to="/datenschutz">{{ t("landing.actions.privacy") }}</RouterLink>
          <BuyMeCoffeeButton />
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.app-shell-wrap {
  min-height: 100vh;
  background: radial-gradient(
      circle at 92% 0%,
      hsl(var(--accent) / 0.3),
      transparent 40%
    ),
    radial-gradient(circle at 8% 95%, hsl(var(--primary) / 0.16), transparent 38%),
    linear-gradient(
      180deg,
      hsl(var(--background)) 0%,
      hsl(var(--muted) / 0.18) 100%
    );
}

footer :deep(.buy-me-coffee-slot) {
  min-height: 40px;
}

footer :deep(.bmc-button) {
  font-size: 0.75rem;
  padding: 0.45rem 0.65rem;
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

.landing-footer-links a:hover {
  text-decoration: underline;
}
</style>
