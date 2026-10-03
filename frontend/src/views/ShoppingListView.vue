<script setup lang="ts">
import { useRouter } from 'vue-router'
import ShoppingListItems from '../components/ShoppingListItems.vue'
import ShoppingListTotals from '../components/ShoppingListTotals.vue'
import { isDemoData } from '../services/api'
import { useShoppingList } from '../composables/useShoppingList'
const router = useRouter()
const {
  basketProducts,
  knownProducts,
  simulation,
  simulating,
  simulationError,
  changeBasketQuantity,
  removeFromBasket,
  calculateBasket,
  lastViewedProductId,
} = useShoppingList()

function browseProducts() {
  void router.push({ name: 'home' })
}

function viewProduct(productId: number) {
  lastViewedProductId.value = productId
  void router.push({ name: 'product', params: { id: String(productId) } })
}
</script>

<template>
  <div class="mvp-app shopping-list-page">
    <main class="shopping-list-main">
      <section class="shopping-list-hero">
        <div>
          <p class="mvp-eyebrow">SIMULAÇÃO DE COMPRAS</p>
          <h1>Minha lista de compras</h1>
          <p>
            Adicione produtos e compare o valor total estimado em cada supermercado, com base nos
            preços online.
          </p>
        </div>
        <img
          src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=520&q=85"
          alt="Cesta com frutas e verduras frescas"
        />
      </section>

      <ShoppingListItems
        :items="basketProducts"
        title="Produtos da lista"
        @update-quantity="changeBasketQuantity"
        @remove-item="removeFromBasket"
        @view-product="viewProduct"
      >
        <template #actions>
          <button class="shopping-add-product" type="button" @click="browseProducts">
            <span aria-hidden="true">＋</span> Adicionar produto
          </button>
        </template>
        <template #empty-action>
          <button class="shopping-empty-add" type="button" @click="browseProducts">
            Buscar produtos
          </button>
        </template>
      </ShoppingListItems>

      <ShoppingListTotals
        :simulation="simulation"
        :products="knownProducts"
        :item-count="basketProducts.length"
        :loading="simulating"
        :error="simulationError"
        @calculate="calculateBasket"
      />

      <p v-if="isDemoData" class="shopping-demo-disclaimer">
        Dados e preços ilustrativos para a demonstração do MVP.
      </p>
    </main>
  </div>
</template>

<style scoped>
.shopping-list-main {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 14px 0 38px;
}
.shopping-list-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 100px;
  overflow: hidden;
  padding: 17px 21px;
  border-radius: 9px;
  background: #e8f5ee;
}
.shopping-list-hero > div {
  position: relative;
  z-index: 1;
  max-width: 620px;
}
.shopping-list-hero .mvp-eyebrow {
  margin-bottom: 5px;
}
.shopping-list-hero h1 {
  margin: 0;
  color: #25342a;
  font-family: 'DM Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: 0;
}
.shopping-list-hero p:last-child {
  max-width: 600px;
  margin: 5px 0 0;
  color: #6e7d72;
  font-size: 10px;
  line-height: 1.5;
}
.shopping-list-hero img {
  position: absolute;
  right: 12px;
  bottom: -34px;
  width: 175px;
  height: 150px;
  object-fit: cover;
  mix-blend-mode: multiply;
  opacity: 0.9;
}
.shopping-add-product {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 11px;
  border: 0;
  border-radius: 4px;
  background: #138b51;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  white-space: nowrap;
}
.shopping-add-product span {
  font-size: 15px;
}
.shopping-empty-add {
  padding: 8px 12px;
  border: 0;
  border-radius: 4px;
  background: #188b52;
  color: white;
  font-size: 9px;
  font-weight: 700;
}
.shopping-demo-disclaimer {
  margin: -5px 0 0;
  color: #928c7b;
  font-size: 8px;
}
@media (max-width: 760px) {
  .shopping-list-main {
    gap: 12px;
    padding-top: 11px;
  }
  .shopping-list-hero {
    min-height: 100px;
    padding: 14px;
  }
  .shopping-list-hero h1 {
    max-width: 260px;
    font-size: 20px;
  }
  .shopping-list-hero p:last-child {
    max-width: 270px;
    font-size: 9px;
  }
  .shopping-list-hero img {
    right: -12px;
    width: 118px;
    height: 112px;
  }
  .shopping-list-hero > div {
    max-width: calc(100% - 55px);
  }
}
@media (max-width: 480px) {
  .shopping-list-main {
    gap: 10px;
  }
  .shopping-list-hero {
    min-height: 110px;
    padding: 12px;
  }
  .shopping-list-hero h1 {
    font-size: 18px;
  }
  .shopping-list-hero p:last-child {
    font-size: 8px;
  }
  .shopping-list-hero img {
    right: -20px;
    width: 90px;
    height: 88px;
  }
  .shopping-list-hero > div {
    max-width: calc(100% - 36px);
  }
  .shopping-add-product {
    min-height: 29px;
    padding: 0 8px;
    font-size: 8px;
  }
}
</style>
