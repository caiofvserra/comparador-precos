<script setup lang="ts">
import { onMounted } from 'vue'
import { CircleHelp, House, List, MapPin } from '@lucide/vue'
import { useRoute } from 'vue-router'
import { loadCatalog, useShoppingList } from '../composables/useShoppingList'

const { basketCount } = useShoppingList()
const route = useRoute()

onMounted(() => void loadCatalog().catch(() => undefined))
</script>

<template>
  <div class="app-layout">
    <header class="mvp-topbar">
      <RouterLink class="mvp-brand" to="/" aria-label="Preço a Preço, início">
        <span class="mvp-mark" aria-hidden="true"><i></i><i></i><i></i></span>
        <span>preço<span>a</span>preço</span>
      </RouterLink>

      <nav class="mvp-nav" aria-label="Navegação principal">
        <RouterLink to="/" :class="{ active: route.name === 'home' }">
          <House aria-hidden="true" /> Início
        </RouterLink>
        <RouterLink to="/lista" :class="{ active: route.name === 'shopping-list' }">
          <List aria-hidden="true" /> Lista de compras <b>{{ basketCount }}</b>
        </RouterLink>
      </nav>

      <span class="mvp-location"><MapPin aria-hidden="true" /> Preços para Ribeirão Preto, SP</span>

      <a class="mvp-help" href="mailto:suporte@precoapreco.local" aria-label="Ajuda">
        <CircleHelp aria-hidden="true" /> <span>Ajuda</span>
      </a>
    </header>

    <RouterView class="app-route" />

    <footer class="mvp-footer">
      <span>preço<span>a</span>preço</span>
      <span>Valores online sujeitos a atualização.</span>
      <span>RIBEIRÃO PRETO, SP</span>
    </footer>
  </div>
</template>

<style scoped>
.mvp-help {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  color: #7c877f;
  font-size: 9px;
  text-decoration: none;
  white-space: nowrap;
}
.mvp-help svg {
  width: 14px;
  height: 14px;
}
@media (max-width: 760px) {
  .mvp-help span {
    display: none;
  }
}
@media (max-width: 1100px) {
  .mvp-location {
    display: none;
  }
}
</style>
