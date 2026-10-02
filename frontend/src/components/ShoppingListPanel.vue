<script setup lang="ts">
import ShoppingListItems from './ShoppingListItems.vue'
import ShoppingListTotals from './ShoppingListTotals.vue'
import type { ShoppingListEntry } from '../composables/useShoppingList'
import type { Product, Simulation } from '../services/api'

defineProps<{
  items: ShoppingListEntry[]
  products: Product[]
  simulation: Simulation | null
  itemCount: number
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  updateQuantity: [productId: number, quantity: number]
  removeItem: [productId: number]
  viewProduct: [productId: number]
  calculate: []
  openList: []
  browseProducts: []
}>()
</script>

<template>
  <section
    id="shopping-list"
    class="mvp-basket shopping-list-panel"
    aria-label="Resumo da lista de compras"
  >
    <ShoppingListItems
      :items="items"
      title="Sua lista"
      compact
      @update-quantity="(productId, quantity) => emit('updateQuantity', productId, quantity)"
      @remove-item="(productId) => emit('removeItem', productId)"
      @view-product="(productId) => emit('viewProduct', productId)"
    >
      <template #actions>
        <button class="panel-open-list" type="button" @click="emit('openList')">
          Ver lista <span aria-hidden="true">↗</span>
        </button>
      </template>
      <template #empty-action>
        <button class="panel-add-products" type="button" @click="emit('browseProducts')">
          Adicionar produtos
        </button>
      </template>
    </ShoppingListItems>
    <ShoppingListTotals
      :simulation="simulation"
      :products="products"
      :item-count="itemCount"
      :loading="loading"
      :error="error"
      compact
      :show-heading="false"
      @calculate="emit('calculate')"
    />
    <p class="panel-data-note">Simulação calculada com preços online coletados.</p>
  </section>
</template>

<style scoped>
.shopping-list-panel {
  display: flex;
  flex-direction: column;
  gap: 11px;
  margin-top: 19px;
  padding: 16px 0 0;
  border-top: 1px solid #dfe6df;
  background: transparent;
}
.panel-open-list {
  padding: 4px 0 4px 7px;
  border: 0;
  background: transparent;
  color: #34744e;
  font-size: 8px;
  font-weight: 700;
  white-space: nowrap;
}
.panel-open-list span {
  margin-left: 3px;
  font-size: 11px;
}
.panel-add-products {
  padding: 7px 10px;
  border: 0;
  border-radius: 4px;
  background: #168b53;
  color: #fff;
  font-size: 8px;
  font-weight: 700;
}
.panel-data-note {
  margin: 0;
  color: #939d95;
  font-size: 8px;
  line-height: 1.4;
}
@media (max-width: 760px) {
  .shopping-list-panel {
    margin-top: 11px;
    padding-top: 13px;
  }
}
@media (max-width: 520px) {
  .shopping-list-panel {
    margin-top: 9px;
  }
}
</style>
