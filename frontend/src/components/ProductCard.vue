<script setup lang="ts">
import { Plus, Scale } from '@lucide/vue'
import { ref } from 'vue'
import { productImageUrl, productTitle } from '../composables/useShoppingList'
import type { Product } from '../services/api'

defineProps<{ product: Product }>()
const emit = defineEmits<{ compare: [product: Product]; add: [product: Product] }>()
const imageFailed = ref(false)
</script>

<template>
  <article class="product-card">
    <button
      class="product-card-image"
      type="button"
      :aria-label="`Comparar preços de ${productTitle(product)}`"
      @click="emit('compare', product)"
    >
      <img
        v-if="productImageUrl(product) && !imageFailed"
        :src="productImageUrl(product)"
        :alt="productTitle(product)"
        @error="imageFailed = true"
      />
      <span v-else class="product-image-fallback"
        ><strong>{{ productTitle(product) }}</strong
        ><small>Imagem indisponível</small></span
      >
    </button>
    <div class="product-card-copy">
      <h3>{{ productTitle(product) }}</h3>
      <p>{{ product.marca || 'Marca não informada' }}</p>
    </div>
    <div class="product-card-actions">
      <button class="product-compare" type="button" @click="emit('compare', product)">
        <Scale :size="14" aria-hidden="true" /> Comparar preços
      </button>
      <button
        class="product-add"
        type="button"
        :aria-label="`Adicionar ${productTitle(product)} à lista`"
        title="Adicionar à lista"
        @click="emit('add', product)"
      >
        <Plus :size="16" aria-hidden="true" />
      </button>
    </div>
  </article>
</template>

<style scoped>
.product-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e6ebe6;
  border-radius: 7px;
  background: #fff;
  box-shadow: 0 2px 5px rgba(38, 53, 45, 0.035);
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}
.product-card:hover {
  border-color: #c1d7c6;
  box-shadow: 0 5px 14px rgba(38, 53, 45, 0.08);
}
.product-card-image {
  display: grid;
  place-items: center;
  width: 100%;
  height: 132px;
  padding: 8px;
  overflow: hidden;
  border: 0;
  background: #fff;
}
.product-card-image img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.product-image-fallback {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  background: #f0f5f0;
  color: #435a49;
  text-align: center;
}
.product-image-fallback strong {
  font-size: 9px;
  line-height: 1.4;
}
.product-image-fallback small {
  color: #87948a;
  font-size: 8px;
}
.product-card-copy {
  padding: 7px 10px 8px;
}
.product-card-copy h3 {
  min-height: 32px;
  margin: 0;
  color: #303b33;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
.product-card-copy p {
  margin: 3px 0 0;
  color: #7c877f;
  font-size: 9px;
}
.product-card-actions {
  display: flex;
  gap: 5px;
  margin-top: auto;
  padding: 0 8px 8px;
}
.product-compare {
  display: flex;
  width: 100%;
  min-height: 32px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 5px;
  border: 0;
  border-radius: 4px;
  background: #168b53;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  white-space: nowrap;
}
.product-compare:hover {
  background: #117246;
}
.product-add {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid #d9e2da;
  background: #fff;
  color: #28654e;
}
.product-add:hover {
  border-color: #28654e;
  background: #edf3ed;
}
@media (max-width: 520px) {
  .product-card-image {
    height: 112px;
    padding: 7px;
  }
  .product-card-copy {
    padding: 6px 7px 7px;
  }
  .product-card-copy h3 {
    min-height: 30px;
    font-size: 9px;
  }
  .product-card-copy p {
    font-size: 8px;
  }
  .product-card-actions {
    padding: 0 6px 6px;
  }
  .product-compare {
    min-height: 30px;
    gap: 4px;
    font-size: 8px;
  }
  .product-add {
    width: 30px;
    height: 30px;
  }
}
</style>
