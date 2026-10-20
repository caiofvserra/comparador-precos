<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import ShoppingListItems from '../components/ShoppingListItems.vue'
import { useShoppingList } from '../composables/useShoppingList'
import { isDemoData } from '../services/api'

const router = useRouter()
const { basketProducts, basketCount, changeBasketQuantity, removeFromBasket, lastViewedProductId } =
  useShoppingList()

const productCountLabel = computed(() => {
  const count = basketProducts.value.length
  return `${count} ${count === 1 ? 'produto' : 'produtos'}`
})

function browseProducts() {
  void router.push({ name: 'catalog', hash: '#product-search' })
}

function compareList() {
  if (!basketProducts.value.length) return
  void router.push({ name: 'comparison' })
}

function viewProduct(productId: number) {
  lastViewedProductId.value = productId
  void router.push({ name: 'product', params: { id: String(productId) } })
}
</script>

<template>
  <div class="mvp-app shopping-list-page">
    <main class="shopping-list-main">
      <section class="shopping-list-hero" aria-labelledby="shopping-list-title">
        <div class="shopping-list-hero-copy">
          <p class="mvp-eyebrow">ORGANIZE SUA COMPRA</p>
          <h1 id="shopping-list-title">Minha lista de compras</h1>
          <p>
            Escolha os produtos e as quantidades que você precisa. Depois, compare a lista completa
            entre os supermercados.
          </p>
          <div class="shopping-list-hero-actions">
            <button class="shopping-add-product" type="button" @click="browseProducts">
              <span aria-hidden="true">＋</span> Adicionar produtos
            </button>
            <span class="shopping-list-note">Organize primeiro. Compare depois.</span>
          </div>
        </div>
        <img
          src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=720&q=85"
          alt="Produtos frescos em um supermercado"
        />
      </section>

      <section class="shopping-list-summary" aria-label="Resumo da lista">
        <div class="shopping-summary-icon" aria-hidden="true">☷</div>
        <div class="shopping-summary-copy">
          <strong>Sua lista está {{ basketProducts.length ? 'em andamento' : 'vazia' }}</strong>
          <span
            >{{ productCountLabel }} · {{ basketCount }}
            {{ basketCount === 1 ? 'unidade' : 'unidades' }} no total</span
          >
        </div>
        <p>Os preços e os totais dos mercados ficam na comparação.</p>
      </section>

      <ShoppingListItems
        :items="basketProducts"
        title="Produtos da lista"
        @update-quantity="changeBasketQuantity"
        @remove-item="removeFromBasket"
        @view-product="viewProduct"
      >
        <template #empty-action>
          <button class="shopping-empty-add" type="button" @click="browseProducts">
            Buscar produtos
          </button>
        </template>
      </ShoppingListItems>

      <section class="shopping-list-next-step" aria-label="Próximo passo">
        <div class="shopping-next-icon" aria-hidden="true">↗</div>
        <div class="shopping-next-copy">
          <strong>Pronto para descobrir onde compensa comprar?</strong>
          <span>A comparação usa os itens e as quantidades desta lista.</span>
        </div>
        <button
          class="shopping-compare-button"
          type="button"
          :disabled="!basketProducts.length"
          @click="compareList"
        >
          Comparar minha lista <span aria-hidden="true">→</span>
        </button>
      </section>

      <p v-if="isDemoData" class="shopping-demo-disclaimer">
        Os produtos e preços desta versão são demonstrativos; os valores serão apresentados na aba
        de comparação.
      </p>
    </main>
  </div>
</template>

<style scoped>
.shopping-list-main {
  display: flex;
  flex-direction: column;
  gap: 17px;
  padding: 20px 0 38px;
}
.shopping-list-hero {
  position: relative;
  display: flex;
  min-height: 190px;
  align-items: center;
  overflow: hidden;
  padding: 27px 30px;
  border: 1px solid #dcece3;
  border-radius: 15px;
  background: linear-gradient(115deg, #f8fcfa 0%, #eaf7f0 62%, #e5f4eb 100%);
  box-shadow: var(--mvp-shadow);
  isolation: isolate;
}
.shopping-list-hero-copy {
  position: relative;
  z-index: 1;
  max-width: 690px;
}
.shopping-list-hero .mvp-eyebrow {
  margin-bottom: 8px;
  color: #398166;
}
.shopping-list-hero h1 {
  margin: 0;
  color: #173250;
  font-size: clamp(26px, 2.2vw, 32px);
  font-weight: 800;
  letter-spacing: -0.8px;
  line-height: 1.15;
}
.shopping-list-hero p:not(.mvp-eyebrow) {
  max-width: 610px;
  margin: 10px 0 0;
  color: #63786e;
  font-size: 12px;
  line-height: 1.7;
}
.shopping-list-hero img {
  position: absolute;
  z-index: -1;
  top: 0;
  right: 0;
  width: 39%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}
.shopping-list-hero::after {
  position: absolute;
  z-index: 0;
  inset: 0;
  background: linear-gradient(
    90deg,
    #f8fcfa 0%,
    rgb(248 252 250 / 97%) 43%,
    rgb(248 252 250 / 65%) 65%,
    rgb(248 252 250 / 0%) 100%
  );
  content: '';
}
.shopping-list-hero-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 18px;
}
.shopping-add-product,
.shopping-empty-add {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 14px;
  border: 0;
  border-radius: 8px;
  background: #087c59;
  color: #fff;
  font-size: 11px;
  font-weight: 750;
  transition:
    background 150ms ease,
    transform 150ms ease;
}
.shopping-add-product:hover,
.shopping-empty-add:hover {
  transform: translateY(-1px);
  background: #066a4c;
}
.shopping-add-product span {
  font-size: 17px;
  line-height: 1;
}
.shopping-list-note {
  color: #71877b;
  font-size: 10px;
}
.shopping-list-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 17px;
  border: 1px solid #e1e9f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: var(--mvp-shadow);
}
.shopping-summary-icon {
  display: grid;
  width: 39px;
  height: 39px;
  flex: 0 0 39px;
  place-items: center;
  border-radius: 11px;
  background: #e8f6ef;
  color: #087c59;
  font-size: 23px;
  font-weight: 800;
}
.shopping-summary-copy {
  display: flex;
  min-width: 185px;
  flex-direction: column;
  gap: 5px;
}
.shopping-summary-copy strong {
  color: #18324d;
  font-size: 12px;
}
.shopping-summary-copy span {
  color: #75879a;
  font-size: 10px;
}
.shopping-list-summary > p {
  margin: 0 0 0 auto;
  color: #75879a;
  font-size: 10px;
  line-height: 1.5;
  text-align: right;
}
.shopping-list-next-step {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 17px;
  border: 1px solid #d8ece1;
  border-radius: 13px;
  background: linear-gradient(100deg, #eff9f3 0%, #f9fcfa 100%);
}
.shopping-next-icon {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  place-items: center;
  border-radius: 50%;
  background: #d9f1e4;
  color: #087c59;
  font-size: 22px;
  font-weight: 800;
}
.shopping-next-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 5px;
}
.shopping-next-copy strong {
  color: #183b32;
  font-size: 12px;
}
.shopping-next-copy span {
  color: #6f8378;
  font-size: 10px;
  line-height: 1.5;
}
.shopping-compare-button {
  display: inline-flex;
  min-height: 40px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 16px;
  border: 0;
  border-radius: 8px;
  background: #087c59;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  box-shadow: 0 4px 12px rgb(8 124 89 / 15%);
}
.shopping-compare-button:hover:not(:disabled) {
  background: #066a4c;
}
.shopping-compare-button:disabled {
  cursor: not-allowed;
  background: #a4b7af;
  box-shadow: none;
}
.shopping-demo-disclaimer {
  margin: -4px 0 0;
  color: #7d8da0;
  font-size: 10px;
  line-height: 1.5;
}
@media (max-width: 760px) {
  .shopping-list-main {
    gap: 13px;
    padding-top: 15px;
  }
  .shopping-list-hero {
    min-height: 175px;
    padding: 20px;
  }
  .shopping-list-hero h1 {
    max-width: 390px;
    font-size: 25px;
  }
  .shopping-list-hero p:not(.mvp-eyebrow) {
    max-width: 430px;
    font-size: 11px;
  }
  .shopping-list-hero img {
    width: 42%;
    opacity: 0.58;
  }
  .shopping-list-hero::after {
    background: linear-gradient(
      90deg,
      #f8fcfa 0%,
      rgb(248 252 250 / 94%) 58%,
      rgb(248 252 250 / 30%) 100%
    );
  }
  .shopping-list-summary {
    flex-wrap: wrap;
  }
  .shopping-list-summary > p {
    flex-basis: 100%;
    margin-left: 51px;
    text-align: left;
  }
  .shopping-list-next-step {
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .shopping-compare-button {
    width: 100%;
  }
}
@media (max-width: 480px) {
  .shopping-list-hero {
    min-height: 190px;
    padding: 17px;
  }
  .shopping-list-hero h1 {
    font-size: 22px;
  }
  .shopping-list-hero p:not(.mvp-eyebrow) {
    max-width: 300px;
    font-size: 10px;
  }
  .shopping-list-hero img {
    width: 55%;
    opacity: 0.35;
  }
  .shopping-list-hero-actions {
    align-items: flex-start;
    flex-direction: column;
    gap: 9px;
  }
  .shopping-summary-copy {
    min-width: 0;
  }
  .shopping-list-summary > p {
    margin-left: 0;
  }
  .shopping-list-next-step {
    padding: 13px;
  }
}
</style>
