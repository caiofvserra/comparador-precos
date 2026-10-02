<script setup lang="ts">
import { ref } from 'vue'
import type { ShoppingListEntry } from '../composables/useShoppingList'

withDefaults(
  defineProps<{
    items: ShoppingListEntry[]
    title: string
    compact?: boolean
  }>(),
  { compact: false },
)

const emit = defineEmits<{
  updateQuantity: [productId: number, quantity: number]
  removeItem: [productId: number]
  viewProduct: [productId: number]
}>()
const failedImages = ref<number[]>([])

function onImageError(productId: number) {
  if (!failedImages.value.includes(productId)) failedImages.value.push(productId)
}
</script>

<template>
  <section class="shopping-items" :class="{ compact }" aria-label="Itens da lista de compras">
    <header class="shopping-items-heading">
      <div>
        <p v-if="!compact" class="items-kicker">SUA COMPRA</p>
        <h2>
          {{ title }} <span>({{ items.length }} {{ items.length === 1 ? 'item' : 'itens' }})</span>
        </h2>
      </div>
      <slot name="actions"></slot>
    </header>

    <div v-if="!items.length" class="shopping-items-empty">
      <span aria-hidden="true">＋</span>
      <strong>Sua lista está vazia</strong>
      <p>Adicione produtos do catálogo para comparar os mercados.</p>
      <slot name="empty-action"></slot>
    </div>

    <div v-else class="shopping-items-rows">
      <article v-for="item in items" :key="item.produto_id" class="shopping-item-row">
        <button
          class="shopping-item-photo"
          type="button"
          :aria-label="`Ver ${item.product?.nome || `produto ${item.produto_id}`}`"
          @click="emit('viewProduct', item.produto_id)"
        >
          <img
            v-if="item.imageUrl && !failedImages.includes(item.produto_id)"
            :src="item.imageUrl"
            alt=""
            @error="onImageError(item.produto_id)"
          />
          <span v-else aria-hidden="true">{{ item.product?.nome?.slice(0, 1) || '•' }}</span>
        </button>

        <div class="shopping-item-name">
          <button type="button" @click="emit('viewProduct', item.produto_id)">
            {{ item.product?.nome || `Produto ${item.produto_id}` }}
          </button>
          <small>{{ item.product?.marca || 'Marca não informada' }}</small>
        </div>

        <div
          class="shopping-quantity"
          :aria-label="`Quantidade de ${item.product?.nome || 'produto'}`"
        >
          <button
            type="button"
            :aria-label="`Diminuir quantidade de ${item.product?.nome || 'produto'}`"
            :disabled="item.quantidade <= 1"
            @click="emit('updateQuantity', item.produto_id, item.quantidade - 1)"
          >
            −
          </button>
          <input
            type="number"
            min="1"
            max="1000"
            :aria-label="`Quantidade de ${item.product?.nome || 'produto'}`"
            :value="item.quantidade"
            @change="
              emit(
                'updateQuantity',
                item.produto_id,
                Number(($event.target as HTMLInputElement).value),
              )
            "
          />
          <button
            type="button"
            :aria-label="`Aumentar quantidade de ${item.product?.nome || 'produto'}`"
            :disabled="item.quantidade >= 1000"
            @click="emit('updateQuantity', item.produto_id, item.quantidade + 1)"
          >
            ＋
          </button>
        </div>
        <span class="shopping-unit">{{ item.quantidade === 1 ? 'unidade' : 'unidades' }}</span>
        <button
          class="shopping-remove"
          type="button"
          :aria-label="`Remover ${item.product?.nome || 'produto'} da lista`"
          title="Remover item"
          @click="emit('removeItem', item.produto_id)"
        >
          ×
        </button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.shopping-items {
  min-width: 0;
  overflow: hidden;
  border: 1px solid #e4eae4;
  border-radius: 7px;
  background: #fff;
}
.shopping-items-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 49px;
  padding: 9px 14px;
  border-bottom: 1px solid #e9eee9;
}
.items-kicker {
  margin: 0 0 3px;
  color: #6f8776;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.8px;
}
.shopping-items-heading h2 {
  margin: 0;
  color: #2e3d33;
  font-size: 13px;
  font-weight: 700;
}
.shopping-items-heading h2 span {
  color: #8a948c;
  font-size: 10px;
  font-weight: 400;
}
.shopping-items-rows {
  padding: 0 13px;
}
.shopping-item-row {
  display: grid;
  grid-template-columns: 42px minmax(130px, 1fr) 84px 62px 24px;
  align-items: center;
  gap: 12px;
  min-height: 66px;
  border-bottom: 1px solid #edf0ed;
}
.shopping-item-row:last-child {
  border-bottom: 0;
}
.shopping-item-photo {
  display: grid;
  place-items: center;
  width: 38px;
  height: 46px;
  overflow: hidden;
  padding: 3px;
  border: 0;
  background: #f8faf7;
  color: #3d7550;
  font-size: 18px;
}
.shopping-item-photo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.shopping-item-name {
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: start;
  gap: 4px;
}
.shopping-item-name button {
  max-width: 100%;
  overflow: hidden;
  padding: 0;
  border: 0;
  background: transparent;
  color: #303d33;
  font-size: 10px;
  font-weight: 600;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.shopping-item-name small {
  color: #858f88;
  font-size: 9px;
}
.shopping-quantity {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 29px;
  border: 1px solid #e3e9e3;
  border-radius: 4px;
}
.shopping-quantity button {
  display: grid;
  place-items: center;
  width: 26px;
  height: 27px;
  padding: 0;
  border: 0;
  background: #fff;
  color: #54655a;
  font-size: 14px;
}
.shopping-quantity button:disabled {
  color: #c6ccc7;
  cursor: default;
}
.shopping-quantity input {
  width: 29px;
  height: 27px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #36453a;
  font-size: 10px;
  text-align: center;
  appearance: textfield;
}
.shopping-quantity input::-webkit-inner-spin-button,
.shopping-quantity input::-webkit-outer-spin-button {
  margin: 0;
  appearance: none;
}
.shopping-unit {
  color: #89938c;
  font-size: 9px;
}
.shopping-remove {
  display: grid;
  place-items: center;
  width: 24px;
  height: 28px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #cc6257;
  font-size: 19px;
}
.shopping-items-empty {
  display: flex;
  min-height: 170px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  text-align: center;
}
.shopping-items-empty > span {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid #dbe6dc;
  border-radius: 50%;
  color: #378256;
  font-size: 20px;
}
.shopping-items-empty strong {
  margin-top: 9px;
  color: #435047;
  font-size: 11px;
}
.shopping-items-empty p {
  margin: 5px 0 10px;
  color: #89938c;
  font-size: 9px;
}
.shopping-items-empty :deep(button) {
  padding: 8px 12px;
  border: 0;
  border-radius: 4px;
  background: #188b52;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
}
.shopping-items.compact {
  border: 0;
  border-radius: 0;
  background: transparent;
}
.shopping-items.compact .shopping-items-heading {
  min-height: 34px;
  padding: 0 0 10px;
  border-bottom: 1px solid #e9ede8;
}
.shopping-items.compact .shopping-items-heading h2 {
  font-size: 11px;
}
.shopping-items.compact .shopping-items-heading h2 span {
  font-size: 9px;
}
.shopping-items.compact .shopping-items-rows {
  padding: 0;
}
.shopping-items.compact .shopping-item-row {
  grid-template-columns: 31px minmax(50px, 1fr) auto 20px;
  gap: 5px;
  min-height: 51px;
}
.shopping-items.compact .shopping-item-photo {
  width: 29px;
  height: 36px;
}
.shopping-items.compact .shopping-item-name button {
  font-size: 9px;
}
.shopping-items.compact .shopping-item-name small {
  font-size: 8px;
}
.shopping-items.compact .shopping-quantity {
  height: 26px;
}
.shopping-items.compact .shopping-quantity button {
  width: 20px;
  height: 24px;
}
.shopping-items.compact .shopping-quantity input {
  width: 22px;
  height: 24px;
}
.shopping-items.compact .shopping-unit {
  display: none;
}
.shopping-items.compact .shopping-remove {
  width: 20px;
}
.shopping-items.compact .shopping-items-empty {
  min-height: 82px;
  padding: 10px 4px;
}
.shopping-items.compact .shopping-items-empty > span {
  width: 26px;
  height: 26px;
  font-size: 16px;
}
.shopping-items.compact .shopping-items-empty strong {
  font-size: 9px;
}
.shopping-items.compact .shopping-items-empty p {
  font-size: 8px;
}
@media (max-width: 700px) {
  .shopping-item-row {
    grid-template-columns: 38px minmax(0, 1fr) 86px 24px;
    gap: 8px;
  }
  .shopping-unit {
    display: none;
  }
}
@media (max-width: 420px) {
  .shopping-items-heading {
    padding: 8px 10px;
  }
  .shopping-items-rows {
    padding: 0 8px;
  }
  .shopping-item-row {
    grid-template-columns: 34px minmax(0, 1fr) 80px 20px;
    gap: 6px;
    min-height: 60px;
  }
  .shopping-item-photo {
    width: 32px;
    height: 41px;
  }
  .shopping-item-name button {
    font-size: 9px;
  }
  .shopping-quantity button {
    width: 23px;
  }
  .shopping-quantity input {
    width: 26px;
  }
}
</style>
