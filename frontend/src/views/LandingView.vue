<script setup lang="ts">
import { Eye, EyeOff, X } from "lucide-vue-next";
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
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuth } from "@/composables/useAuth";
import {
  setAppLocale,
  supportedLocales,
  type SupportedLocale,
} from "@/plugins/i18n";
import { useAuthStore } from "@/stores/auth";

const { locale, t } = useI18n();
const { isAuthenticated } = useAuth();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const email = ref("");
const password = ref("");
const passwordVisible = ref(false);
const errorMessage = ref("");

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
  padding: 1rem;
}

.landing-shell {
  margin: 0 auto;
  display: flex;
  min-height: calc(100vh - 2rem);
  max-width: 72rem;
  flex-direction: column;
  gap: clamp(1.4rem, 2vw, 2.2rem);
  border: 1px solid hsl(var(--primary) / 0.22);
  border-radius: 1.35rem;
  background:
    radial-gradient(circle at 0% 100%, hsl(var(--accent) / 0.22), transparent 40%),
    linear-gradient(160deg, hsl(var(--card)) 0%, hsl(var(--muted) / 0.35) 100%);
  box-shadow:
    0 18px 54px hsl(var(--primary) / 0.16),
    inset 0 1px 0 hsl(var(--primary) / 0.1);
  padding: 1.25rem;
  animation: slide-fade 460ms ease-out both;
}

.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  flex-wrap: wrap;
  border-bottom: 1px dashed hsl(var(--border));
  padding-bottom: 0.8rem;
}

.landing-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0.01em;
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
  border-color: hsl(var(--border));
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
  color: hsl(var(--primary));
}

.landing-main {
  display: grid;
  gap: clamp(1.2rem, 3vw, 2rem);
}

.hero {
  position: relative;
  overflow: clip;
  border-radius: 1.2rem;
  border: 1px solid hsl(var(--primary) / 0.24);
  background: radial-gradient(
      circle at 95% 0%,
      hsl(var(--accent) / 0.45),
      transparent 43%
    ),
    linear-gradient(122deg, hsl(var(--card)) 0%, hsl(var(--muted) / 0.36) 100%);
  padding: clamp(1.8rem, 4vw, 2.9rem) clamp(1.25rem, 4vw, 2.6rem);
}

.hero::after {
  content: "";
  position: absolute;
  width: min(62vw, 28rem);
  height: min(62vw, 28rem);
  right: -11rem;
  top: -13rem;
  background: radial-gradient(circle, hsl(var(--primary) / 0.36), transparent 62%);
  pointer-events: none;
}

.hero-kicker {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: hsl(var(--primary));
}

.hero-title {
  margin: 0.55rem 0 0;
  max-width: 17ch;
  font-size: clamp(2.2rem, 6.4vw, 4.6rem);
  font-weight: 700;
  line-height: 0.98;
  text-wrap: pretty;
}

.hero-copy {
  margin: 1rem 0 0;
  max-width: 54ch;
  font-size: clamp(1rem, 1.1vw, 1.12rem);
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  line-height: 1.55;
}

.hero-ctas {
  margin-top: 1.8rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
}

.feature-grid {
  display: grid;
  gap: 0.9rem;
}

.steps-grid {
  display: grid;
  gap: 0.9rem;
}

.feature-card {
  border: 1px solid hsl(var(--border));
  border-radius: 1rem;
  padding: 1.1rem;
  background: hsl(var(--card) / 0.9);
  box-shadow: 0 8px 24px hsl(var(--primary) / 0.07);
}

.feature-card h2 {
  margin: 0.55rem 0 0;
  font-size: clamp(1.06rem, 1.2vw, 1.3rem);
}

.feature-card p {
  margin: 0.5rem 0 0;
  font-size: 0.94rem;
  color: hsl(var(--muted-foreground));
  line-height: 1.55;
}

.step-card {
  position: relative;
  overflow: hidden;
  border: 1px solid hsl(var(--primary) / 0.2);
  border-radius: 1rem;
  padding: 1.1rem;
  background: linear-gradient(
    155deg,
    hsl(var(--card)) 0%,
    hsl(var(--background) / 0.8) 100%
  );
}

.step-number {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: hsl(var(--primary));
}

.step-card h2 {
  margin: 0.4rem 0 0;
  font-size: clamp(1.06rem, 1.2vw, 1.2rem);
}

.step-card p {
  margin: 0.5rem 0 0;
  font-size: 0.94rem;
  color: hsl(var(--muted-foreground));
  line-height: 1.5;
}

.feature-icon {
  height: 1.2rem;
  width: 1.2rem;
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
  text-decoration-color: hsl(var(--primary));
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

@keyframes slide-fade {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (min-width: 768px) {
  .landing-page {
    padding: 1.45rem;
  }

  .landing-shell {
    min-height: calc(100vh - 2.9rem);
    padding: 1.6rem;
  }

  .landing-main {
    grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr);
    align-items: start;
  }

  .hero {
    grid-column: 1 / span 2;
  }

  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-content: start;
  }

  .feature-card:first-child {
    grid-column: 1 / span 2;
  }

  .steps-grid {
    align-content: start;
  }

  .step-card:nth-child(2) {
    margin-left: 1.2rem;
  }

  .step-card:nth-child(3) {
    margin-left: 2.4rem;
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

@media (min-width: 1100px) {
  .hero {
    min-height: 23rem;
  }

  .hero-copy:last-of-type {
    max-width: 40ch;
  }
}

@media (prefers-reduced-motion: reduce) {
  .landing-shell {
    animation: none;
  }
}
</style>
