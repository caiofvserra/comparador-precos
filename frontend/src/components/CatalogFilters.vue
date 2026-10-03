<script setup lang="ts">
import { Search, SlidersHorizontal, X } from '@lucide/vue'

const selectedBrands = defineModel<string[]>('selectedBrands', { required: true })
const selectedCategories = defineModel<string[]>('selectedCategories', { required: true })
const brandSearch = defineModel<string>('brandSearch', { required: true })
const minPrice = defineModel<string>('minPrice', { required: true })
const maxPrice = defineModel<string>('maxPrice', { required: true })

defineProps<{
  brands: [string, number][]
  categories: [string, number][]
  priceRangeError: string
  hasPriceMetadata: boolean
  hasActiveFilters: boolean
}>()

const emit = defineEmits<{ clear: [] }>()
</script>

<template>
  <section class="catalog-filters" aria-labelledby="catalog-filters-title">
    <div class="filters-heading">
      <strong id="catalog-filters-title"
        ><SlidersHorizontal :size="15" aria-hidden="true" /> Filtrar resultados</strong
      ><button v-if="hasActiveFilters" type="button" @click="emit('clear')">
        Limpar filtros <X :size="12" aria-hidden="true" />
      </button>
    </div>
    <section class="filter-section">
      <h2>Categorias</h2>
      <div v-if="categories.length" class="filter-options">
        <label v-for="[category, count] in categories" :key="category" class="filter-option"
          ><input v-model="selectedCategories" type="checkbox" :value="category" /><span>{{
            category
          }}</span
          ><small>{{ count }}</small></label
        >
      </div>
      <p v-else class="filter-note">Categorias não informadas pela API.</p>
    </section>
    <section class="filter-section">
      <h2>Faixa de preço</h2>
      <div class="price-range">
        <label
          ><span>Mín. (R$)</span
          ><input
            v-model="minPrice"
            type="number"
            min="0"
            step="0.01"
            inputmode="decimal"
            aria-label="Preço mínimo"
            placeholder="0,00"
        /></label>
        <span class="range-separator">até</span>
        <label
          ><span>Máx. (R$)</span
          ><input
            v-model="maxPrice"
            type="number"
            min="0"
            step="0.01"
            inputmode="decimal"
            aria-label="Preço máximo"
            placeholder="Sem limite"
        /></label>
      </div>
      <p v-if="priceRangeError" class="filter-error" role="alert">{{ priceRangeError }}</p>
      <p v-else class="filter-note">
        {{
          hasPriceMetadata
            ? 'Filtra pelo menor preço online encontrado.'
            : 'A API não fornece preços para filtrar.'
        }}
      </p>
    </section>
    <section class="filter-section">
      <h2>Marca</h2>
      <label class="brand-search"
        ><Search :size="13" aria-hidden="true" /><span class="visually-hidden">Buscar marca</span
        ><input v-model="brandSearch" type="search" placeholder="Buscar marca..."
      /></label>
      <div v-if="brands.length" class="filter-options">
        <label v-for="[brand, count] in brands" :key="brand" class="filter-option"
          ><input v-model="selectedBrands" type="checkbox" :value="brand" /><span>{{ brand }}</span
          ><small>{{ count }}</small></label
        >
      </div>
      <p v-else class="filter-note">As marcas aparecem com os resultados.</p>
    </section>
  </section>
</template>

<style scoped>
.catalog-filters {
  grid-column: 1;
  grid-row: 1;
  min-width: 0;
  padding-right: 17px;
  border-right: 1px solid #e2e8e2;
}
.filters-heading {
  display: flex;
  min-height: 38px;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5eae5;
}
.filters-heading strong,
.filters-heading button {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #344138;
  font-size: 10px;
  font-weight: 700;
}
.filters-heading strong svg {
  color: #288256;
}
.filters-heading button {
  padding: 4px 0;
  border: 0;
  background: transparent;
  color: #8a958d;
  font-size: 8px;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.filter-section {
  padding: 13px 0;
  border-bottom: 1px solid #e5eae5;
}
.filter-section h2 {
  margin: 0 0 7px;
  color: #455148;
  font-size: 10px;
  font-weight: 700;
}
.filter-options {
  display: flex;
  flex-direction: column;
}
.filter-option {
  display: flex;
  min-height: 25px;
  align-items: center;
  gap: 7px;
  color: #657168;
  font-size: 9px;
  cursor: pointer;
}
.filter-option input {
  width: 13px;
  height: 13px;
  margin: 0;
  accent-color: #258455;
}
.filter-option small {
  margin-left: auto;
  color: #9ba39d;
  font-size: 8px;
}
.price-range {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: end;
  gap: 5px;
}
.price-range label {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}
.price-range label > span {
  color: #7e8981;
  font-size: 7px;
}
.price-range input {
  width: 100%;
  min-width: 0;
  height: 31px;
  padding: 0 6px;
  border: 1px solid #e2e8e2;
  border-radius: 4px;
  background: #fff;
  color: #46534a;
  font-size: 9px;
}
.price-range input::placeholder {
  color: #a1aaa3;
}
.range-separator {
  padding-bottom: 9px;
  color: #89938c;
  font-size: 8px;
}
.filter-note,
.filter-error {
  margin: 7px 0 0;
  color: #929b94;
  font-size: 8px;
  line-height: 1.45;
}
.filter-error {
  color: #a84f43;
}
.brand-search {
  display: flex;
  height: 33px;
  align-items: center;
  gap: 8px;
  margin: 8px 0 5px;
  padding: 0 8px;
  border: 1px solid #e2e8e2;
  border-radius: 4px;
  background: #fff;
  color: #78857c;
}
.brand-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #445249;
  font-size: 9px;
}
.brand-search input::placeholder {
  color: #9ba49d;
}
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  clip-path: inset(50%);
}
@media (max-width: 1180px) {
  .catalog-filters {
    grid-column: 1;
    grid-row: 1;
    padding-right: 0;
    border-right: 0;
    border-bottom: 1px solid #e2e8e2;
  }
}
@media (max-width: 760px) {
  .catalog-filters {
    grid-column: 1;
    grid-row: 1;
  }
  .filter-section {
    padding: 10px 0;
  }
  .filter-options {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    max-height: 116px;
    overflow: auto;
  }
  .filter-option {
    min-height: 24px;
    font-size: 9px;
  }
}
@media (max-width: 520px) {
  .filters-heading {
    min-height: 34px;
  }
  .filter-section {
    padding: 9px 0;
  }
}
</style>
