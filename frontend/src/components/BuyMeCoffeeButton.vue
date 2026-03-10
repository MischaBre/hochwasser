<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();
</script>

<template>
  <a
    class="bmc-button"
    href="https://www.buymeacoffee.com/MicBrey"
    target="_blank"
    rel="noreferrer"
  >
    <span aria-hidden="true">☕</span>
    <span>{{ t("donation.cta") }}</span>
  </a>
</template>

<style scoped>
.bmc-button {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border: 1px solid #000000;
  border-radius: 999px;
  background: #ffdd00;
  color: #000000;
  font-family: Lato, "Avenir Next", "Segoe UI", sans-serif;
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1;
  padding: 0.52rem 0.78rem;
  text-decoration: none;
  transition: transform 120ms ease;
}

.bmc-button:hover {
  transform: translateY(-1px);
}
</style>
