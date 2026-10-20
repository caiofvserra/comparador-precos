<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { List, ShoppingCart } from '@lucide/vue'
import { useRouter } from 'vue-router'
import ShoppingListTotals from '../components/ShoppingListTotals.vue'
import { useShoppingList } from '../composables/useShoppingList'
import { isDemoData } from '../services/api'

const router = useRouter()
const { basketProducts, knownProducts, simulation, simulating, simulationError, calculateBasket } =
  useShoppingList()

const supermarketCountLabel = computed(() => {
  if (!simulation.value) return 'compare os mercados disponíveis'
  const count = simulation.value.supermercados.length
  return `${count} ${count === 1 ? 'supermercado' : 'supermercados'}`
})

onMounted(() => {
  if (basketProducts.value.length && !simulation.value && !simulating.value) {
    void calculateBasket()
  }
})

function browseProducts() {
  void router.push({ name: 'catalog', hash: '#product-search' })
}

function editList() {
  void router.push({ name: 'shopping-list' })
}
</script>

<template>
  <div class="mvp-app comparison-page">
    <main class="comparison-main">
      <section class="comparison-hero" aria-labelledby="shopping-totals-title">
        <div class="comparison-hero-icon" aria-hidden="true"><List /></div>
        <div class="comparison-hero-copy">
          <p class="mvp-eyebrow">COMPRE MELHOR, ECONOMIZE MAIS</p>
          <h1 id="shopping-totals-title">Comparação de Supermercados</h1>
          <p class="comparison-hero-lede">Veja onde sua lista de compras sai mais em conta.</p>
          <div class="comparison-hero-list">
            <span class="comparison-hero-cart" aria-hidden="true"><ShoppingCart /></span>
            <span class="comparison-hero-list-copy">
              <strong>Lista de compras</strong>
              <small
                >{{ basketProducts.length }}
                {{ basketProducts.length === 1 ? 'produto' : 'produtos' }}
                <span aria-hidden="true">·</span> {{ supermarketCountLabel }}</small
              >
            </span>
          </div>
        </div>
        <img
          class="comparison-hero-image"
          src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1200&q=85"
          alt="Carrinho e produtos frescos em um supermercado"
        />
      </section>

      <ShoppingListTotals
        :simulation="simulation"
        :products="knownProducts"
        :item-count="basketProducts.length"
        :loading="simulating"
        :error="simulationError"
        :show-heading="false"
        comparison-mode
        @calculate="calculateBasket"
        @edit-list="editList"
        @browse-products="browseProducts"
      />

      <p v-if="isDemoData" class="comparison-demo-note">
        <span aria-hidden="true">i</span> Os preços exibidos são demonstrativos e não representam
        ofertas em tempo real.
      </p>
    </main>
  </div>
</template>

<style scoped>
.comparison-main {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 21px;
  padding: 20px 0 34px;
}
.comparison-hero {
  position: relative;
  display: grid;
  grid-template-columns: 78px minmax(0, 1fr);
  align-items: start;
  gap: 20px;
  min-height: 171px;
  overflow: hidden;
  padding: 22px 25px;
  border: 1px solid #e5edf2;
  border-radius: 13px;
  background: #fff;
  box-shadow: var(--mvp-shadow);
  isolation: isolate;
}
.comparison-hero::after {
  position: absolute;
  z-index: 0;
  inset: 0;
  background: linear-gradient(
    90deg,
    #fff 0%,
    #fff 37%,
    rgb(255 255 255 / 96%) 47%,
    rgb(255 255 255 / 74%) 60%,
    rgb(255 255 255 / 0%) 100%
  );
  content: '';
}
.comparison-hero-icon {
  position: relative;
  z-index: 1;
  display: grid;
  width: 72px;
  height: 72px;
  place-items: center;
  margin-top: 1px;
  border-radius: 50%;
  background: linear-gradient(145deg, #0a966b, #00674d);
  color: #fff;
  box-shadow: 0 5px 12px rgb(0 103 77 / 18%);
}
.comparison-hero-icon svg {
  width: 31px;
  height: 31px;
  stroke-width: 2.8;
}
.comparison-hero-copy {
  position: relative;
  z-index: 1;
  min-width: 0;
  max-width: 690px;
}
.comparison-hero-copy .mvp-eyebrow {
  margin-bottom: 5px;
  color: #258064;
  font-size: 9px;
}
.comparison-hero-copy h1 {
  margin: 0;
  color: #102b4b;
  font-size: clamp(23px, 2vw, 29px);
  font-weight: 800;
  letter-spacing: -0.9px;
  line-height: 1.18;
}
.comparison-hero-lede {
  margin: 8px 0 13px;
  color: #183b60;
  font-size: 14px;
  line-height: 1.45;
}
.comparison-hero-list {
  display: inline-flex;
  min-width: 245px;
  align-items: center;
  gap: 10px;
  padding: 9px 13px;
  border: 1px solid #e2f2e9;
  border-radius: 9px;
  background: rgb(231 247 239 / 94%);
}
.comparison-hero-cart {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: #087c59;
  color: #fff;
}
.comparison-hero-cart svg {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}
.comparison-hero-list-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.comparison-hero-list-copy strong {
  color: #087452;
  font-size: 11px;
  font-weight: 800;
}
.comparison-hero-list-copy small {
  color: #236b52;
  font-size: 10px;
}
.comparison-hero-list-copy small span {
  margin: 0 3px;
}
.comparison-hero-image {
  position: absolute;
  z-index: -1;
  top: 0;
  right: 0;
  width: 53%;
  height: 100%;
  object-fit: cover;
  object-position: center 53%;
}
.comparison-demo-note {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin: -9px 0 0;
  color: #77899d;
  font-size: 10px;
  line-height: 1.5;
}
.comparison-demo-note > span {
  display: inline-grid;
  width: 15px;
  height: 15px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid #cedae5;
  border-radius: 50%;
  color: #54708e;
  font-size: 9px;
  font-weight: 700;
}
@media (max-width: 900px) {
  .comparison-main {
    gap: 17px;
    padding-top: 16px;
  }
  .comparison-hero {
    grid-template-columns: 60px minmax(0, 1fr);
    gap: 14px;
    min-height: 160px;
    padding: 20px;
  }
  .comparison-hero-icon {
    width: 58px;
    height: 58px;
  }
  .comparison-hero-icon svg {
    width: 25px;
    height: 25px;
  }
  .comparison-hero-image {
    width: 50%;
  }
  .comparison-hero-copy h1 {
    font-size: 23px;
  }
  .comparison-hero-lede {
    max-width: 400px;
    font-size: 12px;
  }
}
@media (max-width: 600px) {
  .comparison-main {
    gap: 14px;
    padding-top: 13px;
  }
  .comparison-hero {
    grid-template-columns: 1fr;
    gap: 11px;
    min-height: 205px;
    padding: 16px;
  }
  .comparison-hero::after {
    background: linear-gradient(
      90deg,
      rgb(255 255 255 / 97%) 0%,
      rgb(255 255 255 / 91%) 58%,
      rgb(255 255 255 / 56%) 100%
    );
  }
  .comparison-hero-icon {
    width: 42px;
    height: 42px;
  }
  .comparison-hero-icon svg {
    width: 21px;
    height: 21px;
  }
  .comparison-hero-copy h1 {
    max-width: 320px;
    font-size: 22px;
  }
  .comparison-hero-lede {
    max-width: 320px;
    margin: 6px 0 10px;
    font-size: 11px;
  }
  .comparison-hero-list {
    min-width: 0;
    padding: 7px 10px;
  }
  .comparison-hero-image {
    width: 100%;
    opacity: 0.6;
  }
}
</style>
