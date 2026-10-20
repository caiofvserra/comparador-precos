<script setup lang="ts">
import { ChartNoAxesColumnIncreasing, House, List, MapPin, Search, ShoppingCart } from '@lucide/vue'
import { computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loadCatalog, useShoppingList } from '../composables/useShoppingList'

const { basketCount } = useShoppingList()
const route = useRoute()
const router = useRouter()

const isHome = computed(() => route.name === 'home')
const isSearch = computed(() => route.name === 'catalog' || route.name === 'product')
const isShoppingList = computed(() => route.name === 'shopping-list')
const isComparison = computed(() => route.name === 'comparison')

async function browseProducts() {
  if (route.name !== 'home') {
    await router.push({ name: 'catalog', hash: '#product-search' })
  } else if (route.hash !== '#product-search') {
    await router.push({ name: 'catalog', hash: '#product-search' })
  }

  await nextTick()
  const searchInput = document.getElementById('product-search') as HTMLInputElement | null
  if (searchInput) {
    searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
    searchInput.focus({ preventScroll: true })
  }
}

onMounted(() => void loadCatalog().catch(() => undefined))
</script>

<template>
  <div class="app-layout">
    <header class="mvp-topbar">
      <RouterLink class="mvp-brand" to="/" aria-label="Comparador de Preços, início">
        <span class="mvp-brand-icon" aria-hidden="true"><ShoppingCart /></span>
        <span class="mvp-brand-copy">
          <strong>Comparador de Preços</strong>
          <small>Supermercados de Ribeirão Preto</small>
        </span>
      </RouterLink>

      <div class="mvp-topbar-location" aria-label="Localização dos preços">
        <MapPin aria-hidden="true" />
        <span>Ribeirão Preto - SP</span>
      </div>
    </header>

    <div class="app-shell">
      <aside class="mvp-sidebar" aria-label="Menu principal">
        <nav class="mvp-sidebar-nav" aria-label="Navegação principal">
          <RouterLink to="/" :class="{ active: isHome }">
            <House aria-hidden="true" />
            <span>Início</span>
          </RouterLink>
          <RouterLink
            to="/buscar#product-search"
            :class="{ active: isSearch }"
            @click.prevent="browseProducts"
          >
            <Search aria-hidden="true" />
            <span>Buscar produtos</span>
          </RouterLink>
          <RouterLink to="/lista" :class="{ active: isShoppingList }">
            <List aria-hidden="true" />
            <span>Minha lista de compras</span>
            <b v-if="basketCount">{{ basketCount }}</b>
          </RouterLink>
          <RouterLink to="/comparacao" :class="{ active: isComparison }">
            <ChartNoAxesColumnIncreasing aria-hidden="true" />
            <span>Comparação de preços</span>
          </RouterLink>
        </nav>

        <div class="mvp-sidebar-promo">
          <ShoppingCart aria-hidden="true" />
          <p>Mais economia<br />para o seu dia a dia!</p>
        </div>
      </aside>

      <div class="app-content">
        <RouterView class="app-route" />

        <footer class="mvp-footer">
          <span>Comparador de Preços</span>
          <span>Valores online sujeitos a atualização.</span>
          <span>RIBEIRÃO PRETO, SP</span>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mvp-brand-icon {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  place-items: center;
  color: var(--mvp-green);
}

.mvp-brand-icon svg {
  width: 36px;
  height: 36px;
  stroke-width: 2.5;
}

.mvp-brand-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mvp-brand-copy strong {
  color: var(--mvp-navy);
  font-size: 18px;
  font-weight: 750;
  letter-spacing: -0.45px;
  line-height: 1.15;
}

.mvp-brand-copy small {
  color: var(--mvp-muted);
  font-size: 11px;
  font-weight: 500;
}

.mvp-topbar-location {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #334b6b;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.mvp-topbar-location svg {
  width: 17px;
  height: 17px;
  color: var(--mvp-navy);
  stroke-width: 2;
}

.mvp-sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mvp-sidebar-nav a {
  position: relative;
  display: flex;
  min-height: 48px;
  align-items: center;
  gap: 13px;
  padding: 0 15px;
  border: 0;
  border-radius: 0 9px 9px 0;
  color: #e5ebf3;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition:
    color 160ms ease,
    background 160ms ease;
}

.mvp-sidebar-nav a::before {
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: 0;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: transparent;
  content: '';
}

.mvp-sidebar-nav a:hover {
  background: rgb(255 255 255 / 7%);
  color: #fff;
}

.mvp-sidebar-nav a.active {
  background: linear-gradient(100deg, rgb(17 164 119 / 42%), rgb(29 137 114 / 34%));
  color: #fff;
  font-weight: 700;
}

.mvp-sidebar-nav a.active::before {
  background: #19bb8b;
}

.mvp-sidebar-nav a > svg {
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
  stroke-width: 2.2;
}

.mvp-sidebar-nav a > span {
  min-width: 0;
}

.mvp-sidebar-nav b {
  display: grid;
  min-width: 20px;
  height: 20px;
  place-items: center;
  margin-left: auto;
  padding: 0 5px;
  border-radius: 99px;
  background: #0e916b;
  color: white;
  font-size: 10px;
  line-height: 1;
}

.mvp-sidebar-promo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  padding: 30px 12px 18px;
  color: #f2f7fb;
  text-align: center;
}

.mvp-sidebar-promo svg {
  width: 38px;
  height: 38px;
  color: #0cb889;
  stroke-width: 2.2;
}

.mvp-sidebar-promo p {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.6;
}

@media (max-width: 980px) {
  .mvp-brand-icon {
    width: 36px;
    height: 36px;
  }

  .mvp-brand-icon svg {
    width: 31px;
    height: 31px;
  }

  .mvp-brand-copy strong {
    font-size: 16px;
  }

  .mvp-sidebar {
    flex-basis: 215px;
    width: 215px;
  }

  .mvp-sidebar-nav a {
    gap: 10px;
    padding: 0 12px;
    font-size: 12px;
  }
}

@media (max-width: 900px) {
  .mvp-brand-copy small {
    font-size: 10px;
  }

  .mvp-topbar-location {
    gap: 5px;
    font-size: 10px;
  }

  .mvp-sidebar-promo {
    display: none;
  }

  .mvp-sidebar-nav {
    flex-direction: row;
    justify-content: space-around;
    gap: 4px;
  }

  .mvp-sidebar-nav a {
    min-width: 0;
    min-height: 54px;
    flex: 1 1 0;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    padding: 5px 2px;
    border-radius: 8px;
    font-size: 9px;
    text-align: center;
  }

  .mvp-sidebar-nav a::before {
    top: auto;
    right: 10px;
    bottom: 0;
    left: 10px;
    width: auto;
    height: 3px;
    border-radius: 3px 3px 0 0;
  }

  .mvp-sidebar-nav a > svg {
    width: 19px;
    height: 19px;
  }

  .mvp-sidebar-nav a > span {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .mvp-sidebar-nav b {
    position: absolute;
    top: 1px;
    right: calc(50% - 22px);
    min-width: 16px;
    height: 16px;
    font-size: 8px;
  }
}

@media (max-width: 420px) {
  .mvp-brand {
    gap: 5px;
  }

  .mvp-brand-icon {
    width: 31px;
    height: 31px;
  }

  .mvp-brand-icon svg {
    width: 28px;
    height: 28px;
  }

  .mvp-brand-copy strong {
    font-size: 13px;
    letter-spacing: -0.25px;
  }

  .mvp-brand-copy small {
    font-size: 8px;
  }

  .mvp-topbar-location span {
    max-width: 84px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
