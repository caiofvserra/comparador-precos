<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import CatalogFilters from './components/CatalogFilters.vue'
import ProductCard from './components/ProductCard.vue'
import ShoppingListPanel from './components/ShoppingListPanel.vue'
import {
  addToBasket,
  calculateBasket as runSimulation,
  changeBasketQuantity as changeQuantity,
  loadCatalog,
  removeFromBasket,
  searchCatalog,
  useShoppingList,
} from './composables/useShoppingList'
import { isDemoData, type Product } from './services/api'

const search = ref('')
const brandSearch = ref('')
const selectedBrands = ref<string[]>([])
const selectedCategories = ref<string[]>([])
const minPrice = ref('')
const maxPrice = ref('')
const products = ref<Product[]>([])
const router = useRouter()
const {
  basketProducts,
  knownProducts,
  lastViewedProductId,
  simulation,
  simulationError,
  simulating,
} = useShoppingList()
const loadingProducts = ref(false)
const productsError = ref('')
let searchTimer: ReturnType<typeof setTimeout> | undefined
let searchSequence = 0
const brandOptions = computed(() => {
  const counts = new Map<string, number>()
  for (const product of products.value) {
    if (product.marca) counts.set(product.marca, (counts.get(product.marca) ?? 0) + 1)
  }
  return [...counts.entries()]
    .sort(([first], [second]) => first.localeCompare(second, 'pt-BR'))
    .filter(([brand]) =>
      brand.toLocaleLowerCase('pt-BR').includes(brandSearch.value.toLocaleLowerCase('pt-BR')),
    )
})
const categoryOptions = computed(() => {
  const counts = new Map<string, number>()
  for (const product of knownProducts.value) {
    for (const category of product.categorias ?? []) {
      counts.set(category, (counts.get(category) ?? 0) + 1)
    }
  }
  return [...counts.entries()].sort(([first], [second]) => first.localeCompare(second, 'pt-BR'))
})
const priceRangeError = computed(() => {
  const minimum = minPrice.value === '' ? null : Number(minPrice.value)
  const maximum = maxPrice.value === '' ? null : Number(maxPrice.value)
  if (minimum !== null && (!Number.isFinite(minimum) || minimum < 0))
    return 'Informe um mínimo igual ou maior que zero.'
  if (maximum !== null && (!Number.isFinite(maximum) || maximum < 0))
    return 'Informe um máximo igual ou maior que zero.'
  if (minimum !== null && maximum !== null && minimum > maximum)
    return 'O preço mínimo deve ser menor que o máximo.'
  return ''
})
const hasCatalogFilters = computed(
  () =>
    selectedBrands.value.length > 0 ||
    selectedCategories.value.length > 0 ||
    minPrice.value !== '' ||
    maxPrice.value !== '',
)
const hasPriceMetadata = computed(() =>
  knownProducts.value.some((product) => product.preco_minimo !== undefined),
)
const visibleProducts = computed(() =>
  products.value.filter((product) => {
    if (priceRangeError.value) return false
    if (
      selectedBrands.value.length &&
      (!product.marca || !selectedBrands.value.includes(product.marca))
    )
      return false
    if (
      selectedCategories.value.length &&
      !product.categorias?.some((category) => selectedCategories.value.includes(category))
    )
      return false
    if (minPrice.value === '' && maxPrice.value === '') return true
    if (product.preco_minimo === undefined || product.preco_minimo === null) return false
    const lowestPrice = Number(product.preco_minimo)
    if (minPrice.value !== '' && lowestPrice < Number(minPrice.value)) return false
    if (maxPrice.value !== '' && lowestPrice > Number(maxPrice.value)) return false
    return true
  }),
)

function formatRangePrice(value: string) {
  return Number(value).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

async function searchProducts(query = search.value) {
  const currentSequence = ++searchSequence
  loadingProducts.value = true
  productsError.value = ''
  try {
    const result = await searchCatalog(query)
    if (currentSequence === searchSequence) products.value = result
  } catch (error) {
    if (currentSequence === searchSequence) {
      productsError.value = error instanceof Error ? error.message : 'Falha ao buscar produtos.'
    }
  } finally {
    if (currentSequence === searchSequence) loadingProducts.value = false
  }
}

async function openShoppingList() {
  await router.push({ name: 'shopping-list' })
}

async function browseProducts() {
  await router.push({ name: 'home' })
  await nextTick()
  document.getElementById('product-search')?.focus()
}

async function viewProductById(productId: number) {
  lastViewedProductId.value = productId
  await router.push({ name: 'product', params: { id: String(productId) } })
}

async function compareProduct(product: Product) {
  lastViewedProductId.value = product.id
  await router.push({ name: 'product', params: { id: String(product.id) } })
}

function clearFilters() {
  brandSearch.value = ''
  selectedBrands.value = []
  selectedCategories.value = []
  minPrice.value = ''
  maxPrice.value = ''
}

function searchExample(query: string) {
  search.value = query
  void searchProducts(query)
}

watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => void searchProducts(), 220)
})

onMounted(async () => {
  try {
    const result = await loadCatalog()
    products.value = result
  } catch {
    productsError.value = 'Não foi possível carregar os produtos.'
  }
})
</script>

<template>
  <div class="mvp-app home-page">
    <main class="mvp-main" id="inicio">
      <section class="mvp-hero">
        <div class="mvp-hero-copy">
          <p class="mvp-eyebrow">PESQUISA DE PREÇOS ONLINE</p>
          <h1>Pesquise produtos e compare preços de vários supermercados</h1>
          <p class="mvp-lede">
            Encontre preços online em Ribeirão Preto, confira as fontes e simule sua lista.
          </p>
        </div>
        <div class="mvp-hero-search-area">
          <form class="mvp-search" role="search" @submit.prevent="searchProducts()">
            <span class="mvp-search-icon" aria-hidden="true"></span>
            <label class="visually-hidden" for="product-search">Buscar produto ou marca</label>
            <input
              id="product-search"
              v-model="search"
              type="search"
              placeholder="Digite o nome de um produto (ex.: arroz, leite, café...)"
            />
            <button type="submit" aria-label="Buscar produtos">Buscar</button>
          </form>
          <div class="mvp-search-examples">
            <span>Exemplos de busca:</span
            ><button
              v-for="example in ['arroz', 'leite', 'café', 'azeite', 'pão', 'banana']"
              :key="example"
              type="button"
              @click="searchExample(example)"
            >
              {{ example }}
            </button>
          </div>
          <div v-if="isDemoData" class="mvp-demo-note">
            <span aria-hidden="true">i</span
            ><strong>Preços ilustrativos, não são ofertas atuais.</strong>
          </div>
        </div>
        <img
          class="mvp-hero-image"
          src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=520&q=85"
          alt="Cesta com frutas e verduras frescas"
        />
      </section>

      <div class="mvp-workspace">
        <div class="mvp-catalog">
          <section class="mvp-results" aria-labelledby="results-title">
            <div class="mvp-section-head">
              <div>
                <p class="mvp-eyebrow">CATÁLOGO</p>
                <h2 id="results-title">
                  {{ visibleProducts.length }}
                  {{ visibleProducts.length === 1 ? 'produto encontrado' : 'produtos encontrados'
                  }}<span v-if="search"> para “{{ search }}”</span>
                </h2>
              </div>
              <span v-if="loadingProducts" class="mvp-inline-state">Buscando…</span>
            </div>
            <p v-if="hasCatalogFilters" class="mvp-filter-summary">
              <span v-if="selectedCategories.length">{{ selectedCategories.join(', ') }}</span>
              <span v-if="selectedBrands.length">{{ selectedBrands.join(', ') }}</span>
              <span v-if="minPrice !== '' || maxPrice !== ''"
                >{{ minPrice !== '' ? `R$ ${formatRangePrice(minPrice)}` : 'Sem mínimo' }} –
                {{ maxPrice !== '' ? `R$ ${formatRangePrice(maxPrice)}` : 'Sem máximo' }}</span
              >
              <button type="button" @click="clearFilters">Remover filtros</button>
            </p>
            <p v-if="productsError" class="mvp-error" role="alert">{{ productsError }}</p>
            <div v-else-if="loadingProducts && !products.length" class="mvp-state">
              Carregando produtos…
            </div>
            <div v-else-if="!visibleProducts.length" class="mvp-state mvp-empty">
              <span aria-hidden="true">⌕</span><strong>Nenhum produto encontrado</strong
              ><small>Tente outro nome ou marca.</small>
            </div>
            <div v-else class="mvp-product-grid">
              <ProductCard
                v-for="product in visibleProducts"
                :key="product.id"
                :product="product"
                @compare="compareProduct"
                @add="addToBasket"
              />
            </div>
          </section>
        </div>

        <aside class="mvp-filter-panel" aria-label="Filtros de busca">
          <CatalogFilters
            v-model:selected-brands="selectedBrands"
            v-model:selected-categories="selectedCategories"
            v-model:brand-search="brandSearch"
            v-model:min-price="minPrice"
            v-model:max-price="maxPrice"
            :brands="brandOptions"
            :categories="categoryOptions"
            :price-range-error="priceRangeError"
            :has-price-metadata="hasPriceMetadata"
            :has-active-filters="hasCatalogFilters"
            @clear="clearFilters"
          />
          <ShoppingListPanel
            :items="basketProducts"
            :products="knownProducts"
            :simulation="simulation"
            :item-count="basketProducts.length"
            :loading="simulating"
            :error="simulationError"
            @update-quantity="changeQuantity"
            @remove-item="removeFromBasket"
            @view-product="viewProductById"
            @calculate="runSimulation"
            @open-list="openShoppingList"
            @browse-products="browseProducts"
          />
        </aside>
      </div>
    </main>
  </div>
</template>

<style>
.mvp-hero {
  display: grid;
  grid-template-columns: minmax(230px, 0.83fr) minmax(340px, 1.45fr) 160px;
  align-items: center;
  gap: 24px;
  min-height: 180px;
  margin: 15px -7.5% 0;
  padding: 22px 7.5%;
  overflow: hidden;
  border-radius: 11px;
  background: #e7f5ee;
}
.mvp-hero-copy,
.mvp-hero-search-area {
  position: relative;
  z-index: 1;
}
.mvp-hero-copy .mvp-eyebrow {
  margin-bottom: 8px;
}
.mvp-app .mvp-hero h1 {
  max-width: 320px;
  font-family: 'DM Sans', sans-serif;
  font-size: 25px;
  font-weight: 700;
  line-height: 1.12;
  letter-spacing: 0;
}
.mvp-lede {
  max-width: 330px;
  margin-top: 9px;
  font-size: 10px;
  line-height: 1.5;
}
.mvp-search {
  display: flex;
  min-width: 0;
  min-height: 54px;
  align-items: center;
  gap: 12px;
  padding: 6px 7px 6px 16px;
  border: 1px solid #d9e1d9;
  border-radius: 6px;
  background: #fff;
}
.mvp-search-icon {
  position: relative;
  width: 15px;
  height: 15px;
  flex: 0 0 auto;
  border: 1.7px solid #67766c;
  border-radius: 50%;
}
.mvp-search-icon::after {
  position: absolute;
  right: -5px;
  bottom: -2px;
  width: 6px;
  height: 1.5px;
  background: #67766c;
  content: '';
  transform: rotate(48deg);
}
.mvp-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--mvp-ink);
  font-size: 11px;
}
.mvp-search input::placeholder { color: #9aa49c; }
.mvp-search button {
  min-height: 38px;
  padding: 0 18px;
  border: 0;
  border-radius: 4px;
  background: #128b51;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
}
.mvp-search button:hover { background: #117246; }
.mvp-hero .mvp-search {
  box-shadow: 0 2px 8px rgba(34, 54, 42, 0.04);
}
.mvp-search-examples {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
  color: #718077;
  font-size: 9px;
}
.mvp-search-examples button {
  padding: 5px 10px;
  border: 1px solid #e1e9e3;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
  color: #5f6e63;
  font-size: 9px;
}
.mvp-search-examples button:hover {
  border-color: #a8c3ae;
  color: var(--mvp-green);
}
.mvp-hero .mvp-demo-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 0;
  border: 0;
  background: transparent;
}
.mvp-hero .mvp-demo-note > span {
  width: 16px;
  height: 16px;
  font-size: 10px;
}
.mvp-hero .mvp-demo-note strong {
  color: #756d5b;
  font-size: 8px;
  font-weight: 500;
}
.mvp-hero-image {
  width: 160px;
  height: 136px;
  align-self: end;
  object-fit: cover;
  object-position: center;
  mix-blend-mode: multiply;
}
.mvp-workspace {
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr);
  gap: 28px;
  padding-top: 24px;
}
.mvp-filter-panel {
  grid-column: 1;
  grid-row: 1;
  min-width: 0;
  padding-right: 17px;
  border-right: 1px solid #e2e8e2;
}
.mvp-catalog {
  grid-column: 2;
  grid-row: 1;
  min-width: 0;
}
.mvp-filter-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 38px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5eae5;
}
.mvp-filter-heading strong {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #344138;
  font-size: 11px;
}
.mvp-filter-heading strong > span {
  color: #288256;
  font-size: 13px;
}
.mvp-filter-heading button {
  padding: 4px 0;
  border: 0;
  background: transparent;
  color: #8a958d;
  font-size: 9px;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.mvp-filter-section {
  padding: 13px 0;
  border-bottom: 1px solid #e5eae5;
}
.mvp-filter-section > summary {
  cursor: pointer;
  color: #455148;
  font-size: 10px;
  font-weight: 700;
  list-style: none;
}
.mvp-filter-section > summary::-webkit-details-marker {
  display: none;
}
.mvp-filter-section > summary::after {
  float: right;
  color: #637369;
  content: '⌃';
}
.mvp-filter-section:not([open]) > summary::after {
  content: '⌄';
}
.mvp-brand-search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 33px;
  margin: 10px 0 7px;
  padding: 0 8px;
  border: 1px solid #e2e8e2;
  border-radius: 4px;
  background: #fff;
  color: #78857c;
}
.mvp-brand-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #445249;
  font-size: 9px;
}
.mvp-brand-search input::placeholder {
  color: #9ba49d;
}
.mvp-brand-options {
  display: flex;
  flex-direction: column;
}
.mvp-category-options {
  display: flex;
  flex-direction: column;
}
.mvp-filter-summary {
  margin: 0 0 8px;
  color: #607068;
  font-size: 9px;
}
.mvp-filter-summary button {
  margin-left: 5px;
  border: 0;
  background: transparent;
  color: var(--mvp-green);
  font-size: 9px;
  text-decoration: underline;
}
.mvp-section-head {
  align-items: center;
  margin-bottom: 12px;
}
.mvp-section-head .mvp-eyebrow {
  display: none;
}
.mvp-app .mvp-section-head h2 {
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 700;
}
.mvp-app .mvp-section-head h2 > span {
  color: inherit;
  font-family: inherit;
  font-size: inherit;
  font-weight: inherit;
}
.mvp-product-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 11px;
}

@media (max-width: 1180px) {
  .mvp-hero {
    grid-template-columns: minmax(210px, 0.8fr) minmax(300px, 1.4fr) 125px;
    gap: 15px;
    margin-right: -5.3%;
    margin-left: -5.3%;
    padding-right: 5.3%;
    padding-left: 5.3%;
  }
  .mvp-hero-image {
    width: 125px;
    height: 120px;
  }
  .mvp-workspace {
    grid-template-columns: 190px minmax(0, 1fr);
    gap: 20px;
  }
  .mvp-product-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 760px) {
  .mvp-hero {
    grid-template-columns: minmax(0, 1fr) 100px;
    gap: 12px;
    min-height: 174px;
    margin: 12px -20px 0;
    padding: 17px 20px;
  }
  .mvp-app .mvp-hero h1 {
    font-size: 20px;
  }
  .mvp-lede {
    max-width: 340px;
    font-size: 9px;
  }
  .mvp-hero-image {
    width: 100px;
    height: 116px;
  }
  .mvp-hero-search-area {
    grid-column: 1 / -1;
  }
  .mvp-hero .mvp-search {
    min-height: 45px;
  }
  .mvp-hero .mvp-search button {
    min-height: 34px;
    padding: 0 14px;
    font-size: 10px;
  }
  .mvp-search-examples {
    gap: 5px;
    margin-top: 7px;
  }
  .mvp-search-examples > span {
    width: 100%;
  }
  .mvp-search-examples button {
    padding: 4px 8px;
    font-size: 8px;
  }
  .mvp-hero .mvp-demo-note {
    position: absolute;
    top: 8px;
    right: 8px;
    max-width: 120px;
  }
  .mvp-hero .mvp-demo-note > span {
    display: none;
  }
  .mvp-hero .mvp-demo-note strong {
    text-align: right;
    font-size: 7px;
  }
  .mvp-workspace {
    grid-template-columns: 1fr;
    gap: 22px;
    padding-top: 20px;
  }
  .mvp-filter-panel {
    grid-column: 1;
    grid-row: 1;
    padding-right: 0;
    border-right: 0;
    border-bottom: 1px solid #e2e8e2;
  }
  .mvp-catalog {
    grid-column: 1;
    grid-row: 2;
  }
  .mvp-filter-heading {
    min-height: 34px;
  }
}
@media (max-width: 520px) {
  .mvp-hero {
    grid-template-columns: 1fr 66px;
    gap: 8px;
    min-height: 0;
    margin: 10px -15px 0;
    padding: 17px 15px 13px;
    border-radius: 8px;
  }
  .mvp-app .mvp-hero h1 {
    max-width: 260px;
    font-size: 19px;
    line-height: 1.15;
  }
  .mvp-hero .mvp-eyebrow {
    font-size: 7px;
  }
  .mvp-lede {
    max-width: 245px;
    margin-top: 6px;
    font-size: 8px;
  }
  .mvp-hero-image {
    width: 66px;
    height: 84px;
    align-self: center;
  }
  .mvp-hero-search-area {
    margin-top: 3px;
  }
  .mvp-hero .mvp-search {
    min-height: 42px;
    gap: 8px;
    padding-left: 10px;
  }
  .mvp-search-icon {
    width: 13px;
    height: 13px;
  }
  .mvp-hero .mvp-search input {
    font-size: 9px;
  }
  .mvp-hero .mvp-search button {
    min-height: 32px;
    padding: 0 10px;
    font-size: 9px;
  }
  .mvp-search-examples {
    gap: 4px;
    font-size: 8px;
  }
  .mvp-search-examples button {
    padding: 4px 7px;
  }
  .mvp-hero .mvp-demo-note {
    top: 5px;
    right: 5px;
    max-width: 92px;
  }
  .mvp-hero .mvp-demo-note strong {
    font-size: 6px;
  }
  .mvp-workspace {
    gap: 16px;
    padding-top: 16px;
  }
  .mvp-filter-panel {
    padding-bottom: 4px;
  }
  .mvp-filter-heading strong {
    font-size: 10px;
  }
  .mvp-filter-heading button {
    font-size: 8px;
  }
  .mvp-app .mvp-section-head h2 {
    font-size: 12px;
  }
  .mvp-section-head {
    align-items: center;
  }
  .mvp-product-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .mvp-app *,
  .mvp-app *::before,
  .mvp-app *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
