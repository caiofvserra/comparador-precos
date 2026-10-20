<script setup lang="ts">
import { Plus, Scale } from '@lucide/vue'
import { ref, watch } from 'vue'
import {
  productFallbackImageUrl,
  productImageUrl,
  productTitle,
} from '../composables/useShoppingList'
import type { Product } from '../services/api'

const props = defineProps<{ product: Product }>()
const emit = defineEmits<{ compare: [product: Product]; add: [product: Product] }>()
const imageFailed = ref(false)
const usingFallback = ref(false)
watch(
  () => props.product.id,
  () => {
    imageFailed.value = false
    usingFallback.value = false
  },
)
function imageSource() {
  return usingFallback.value
    ? productFallbackImageUrl(props.product)
    : productImageUrl(props.product)
}
function handleImageError() {
  const fallback = productFallbackImageUrl(props.product)
  if (!usingFallback.value && imageSource() !== fallback) {
    usingFallback.value = true
    return
  }
  imageFailed.value = true
}
</script>

<template>
  <article class="product-card">
    <button
      class="product-card-image"
      type="button"
      :aria-label="`Comparar preços de ${productTitle(props.product)}`"
      @click="emit('compare', props.product)"
    >
      <img
        v-if="!imageFailed"
        :src="imageSource()"
        :alt="productTitle(props.product)"
        @error="handleImageError"
      />
      <span v-else class="product-image-fallback"
        ><strong>{{ productTitle(props.product) }}</strong
        ><small>Imagem indisponível</small></span
      >
    </button>
    <div class="product-card-copy">
      <h3>{{ productTitle(props.product) }}</h3>
      <p>{{ props.product.marca || 'Marca não informada' }}</p>
    </div>
    <div class="product-card-actions">
      <button class="product-compare" type="button" @click="emit('compare', props.product)">
        <Scale :size="14" aria-hidden="true" /> Comparar preços
      </button>
      <button
        class="product-add"
        type="button"
        :aria-label="`Adicionar ${productTitle(props.product)} à lista`"
        title="Adicionar à lista"
        @click="emit('add', props.product)"
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
  /* Use a predictable frame so the complete product image remains visible. */
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  object-position: center center;
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

/* Visual refinement: shared design language. */

.product-card {
  border-color: #e2e9f1;
  border-radius: 12px;
  box-shadow: 0 3px 12px rgb(25 52 79 / 4%);
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    transform 160ms ease;
}
.product-card:hover {
  border-color: #b4dac8;
  box-shadow: 0 9px 22px rgb(25 52 79 / 9%);
  transform: translateY(-2px);
}
.product-card-image {
  height: 176px;
  padding: 10px;
  background: #fff;
}
.product-image-fallback {
  border-radius: 8px;
  background: #f0f8f3;
  color: #315f4b;
}
.product-image-fallback strong {
  font-size: 11px;
}
.product-image-fallback small {
  font-size: 10px;
}
.product-card-copy {
  padding: 12px 13px 10px;
}
.product-card-copy h3 {
  min-height: 38px;
  color: #203752;
  font-size: 13px;
  line-height: 1.4;
}
.product-card-copy p {
  font-size: 11px;
}
.product-card-actions {
  gap: 8px;
  padding: 0 12px 12px;
}
.product-compare {
  min-height: 38px;
  border-radius: 8px;
  background: #087c59;
  font-size: 11px;
}
.product-compare:hover {
  background: #066848;
}
.product-add {
  width: 38px;
  height: 38px;
  border-color: #dce7e1;
  border-radius: 8px;
  color: #087c59;
}
.product-add:hover {
  border-color: #087c59;
  background: #eaf7f1;
}
@media (max-width: 520px) {
  .product-card-image {
    height: 136px;
    padding: 8px;
  }
  .product-card-copy {
    padding: 8px 9px;
  }
  .product-card-copy h3 {
    min-height: 34px;
    font-size: 11px;
  }
  .product-card-copy p {
    font-size: 9px;
  }
  .product-card-actions {
    gap: 5px;
    padding: 0 8px 8px;
  }
  .product-compare {
    min-height: 32px;
    font-size: 9px;
  }
  .product-add {
    width: 32px;
    height: 32px;
  }
}
</style>
