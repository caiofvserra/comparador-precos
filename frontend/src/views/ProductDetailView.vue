<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getComparison,
  getProductHistory,
  getProducts,
  getSupermarkets,
  isDemoData,
  type Comparison,
  type HistoryEntry,
  type Product,
  type ProductHistory,
  type Supermarket,
} from '../services/api'
import { productImageUrl, useShoppingList } from '../composables/useShoppingList'

const route = useRoute()
const router = useRouter()
const { addToBasket, lastViewedProductId } = useShoppingList()
const product = ref<Product | null>(null)
const comparison = ref<Comparison | null>(null)
const history = ref<ProductHistory | null>(null)
const supermarkets = ref<Supermarket[]>([])
const selectedSupermarket = ref('')
const period = ref('3m')
const startDate = ref('')
const endDate = ref('')
const appliedStartDate = ref('')
const appliedEndDate = ref('')
const loading = ref(true)
const loadingHistory = ref(false)
const productError = ref('')
const comparisonError = ref('')
const historyError = ref('')
const imageFailed = ref(false)
let productRequest = 0
let historyRequest = 0

const storeColors = ['#178b51', '#d48742', '#c95252', '#5988a4', '#8c75a8']

const productName = computed(() => product.value?.nome?.replace(/\s+/g, ' ').trim() || 'Produto')
const productBrand = computed(() => product.value?.marca || 'Marca não informada')
const productImage = computed(() =>
  product.value && !imageFailed.value ? productImageUrl(product.value) : '',
)
const currentPrices = computed(() =>
  [...(comparison.value?.precos ?? [])].sort((first, second) => {
    if (!first.disponivel) return 1
    if (!second.disponivel) return -1
    return Number(first.valor) - Number(second.valor)
  }),
)
const historyRecords = computed(() => {
  const records = history.value?.historico ?? []
  return [...records]
    .filter((entry) => {
      const date = entry.data_hora_coleta.slice(0, 10)
      return (
        (!appliedStartDate.value || date >= appliedStartDate.value) &&
        (!appliedEndDate.value || date <= appliedEndDate.value)
      )
    })
    .sort((first, second) => first.data_hora_coleta.localeCompare(second.data_hora_coleta))
})
const historySummary = computed(() => {
  if (!historyRecords.value.length) return null
  const cheapest = historyRecords.value.reduce((best, entry) =>
    Number(entry.valor) < Number(best.valor) ? entry : best,
  )
  const mostExpensive = historyRecords.value.reduce((best, entry) =>
    Number(entry.valor) > Number(best.valor) ? entry : best,
  )
  const average =
    historyRecords.value.reduce((total, entry) => total + Number(entry.valor), 0) /
    historyRecords.value.length
  return { cheapest, mostExpensive, average, count: historyRecords.value.length }
})
const historyChart = computed(() => {
  const records = historyRecords.value
  if (!records.length) return null
  const dates = records.map((entry) => new Date(entry.data_hora_coleta).getTime())
  const values = records.map((entry) => Number(entry.valor))
  const minDate = Math.min(...dates)
  const maxDate = Math.max(...dates)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const valueRange = maxValue - minValue || 1
  const x = (timestamp: number) => 54 + ((timestamp - minDate) / (maxDate - minDate || 1)) * 675
  const y = (value: number) => 164 - ((value - minValue) / valueRange) * 125
  const groups = new Map<number, HistoryEntry[]>()
  records.forEach((entry) => {
    const group = groups.get(entry.supermercado.id) ?? []
    group.push(entry)
    groups.set(entry.supermercado.id, group)
  })
  const series = [...groups.entries()].map(([id, entries], index) => ({
    id,
    name: entries[0]!.supermercado.nome,
    color: storeColors[index % storeColors.length]!,
    points: entries.map((entry) => ({
      x: x(new Date(entry.data_hora_coleta).getTime()),
      y: y(Number(entry.valor)),
      entry,
    })),
  }))
  const ticks = [
    ...new Map(
      records.map((entry) => [
        entry.data_hora_coleta.slice(0, 10),
        new Date(entry.data_hora_coleta).getTime(),
      ]),
    ).entries(),
  ]
  const tickStep = Math.max(1, Math.ceil(ticks.length / 6))
  const dateTicks = ticks
    .filter((_, index) => index % tickStep === 0 || index === ticks.length - 1)
    .map(([date, timestamp]) => ({
      date,
      x: x(timestamp),
      label: new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        timeZone: 'America/Sao_Paulo',
      }).format(new Date(timestamp)),
    }))
  const priceTicks = Array.from({ length: 5 }, (_, index) => {
    const value = maxValue - (valueRange * index) / 4
    return { value, y: 24 + (140 * index) / 4 }
  })
  return { series, dateTicks, priceTicks }
})

function formatPrice(value: string | number) {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'America/Sao_Paulo',
  }).format(new Date(value))
}

function formatDay(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: 'America/Sao_Paulo',
  }).format(new Date(value))
}

function handleImageError() {
  imageFailed.value = true
}

function setPeriodDates() {
  const records = history.value?.historico ?? []
  const latest = records.reduce(
    (current, entry) => (entry.data_hora_coleta > current ? entry.data_hora_coleta : current),
    '',
  )
  const end = latest ? latest.slice(0, 10) : new Date().toISOString().slice(0, 10)
  const endDateValue = new Date(`${end}T12:00:00`)
  const months =
    period.value === '1m' ? 1 : period.value === '3m' ? 3 : period.value === '6m' ? 6 : 0
  if (months) endDateValue.setMonth(endDateValue.getMonth() - months)
  startDate.value = months ? endDateValue.toISOString().slice(0, 10) : ''
  endDate.value = period.value === 'all' ? '' : end
  applyFilters()
}

function applyFilters() {
  appliedStartDate.value = startDate.value
  appliedEndDate.value = endDate.value
}

async function loadHistory() {
  if (!product.value) return
  const requestId = ++historyRequest
  loadingHistory.value = true
  historyError.value = ''
  try {
    const storeId = selectedSupermarket.value ? Number(selectedSupermarket.value) : undefined
    const result = await getProductHistory(product.value.id, storeId)
    if (requestId === historyRequest) {
      history.value = result
      setPeriodDates()
    }
  } catch (error) {
    if (requestId === historyRequest) {
      historyError.value =
        error instanceof Error ? error.message : 'Não foi possível carregar o histórico.'
    }
  } finally {
    if (requestId === historyRequest) loadingHistory.value = false
  }
}

async function loadProduct() {
  const requestId = ++productRequest
  const id = Number(route.params.id)
  if (!Number.isInteger(id) || id < 1) {
    productError.value = 'Produto não encontrado.'
    loading.value = false
    return
  }
  lastViewedProductId.value = id
  loading.value = true
  productError.value = ''
  comparisonError.value = ''
  historyError.value = ''
  const [productsResult, comparisonResult, historyResult, storesResult] = await Promise.allSettled([
    getProducts(),
    getComparison(id),
    getProductHistory(id),
    getSupermarkets(),
  ])
  if (requestId !== productRequest) return
  if (productsResult.status === 'fulfilled') {
    product.value = productsResult.value.find((item) => item.id === id) ?? null
    if (!product.value) productError.value = 'Este produto não está disponível no catálogo.'
  } else {
    productError.value = 'Não foi possível carregar os dados do produto.'
  }
  if (comparisonResult.status === 'fulfilled') comparison.value = comparisonResult.value
  else
    comparisonError.value =
      comparisonResult.reason instanceof Error
        ? comparisonResult.reason.message
        : 'Não foi possível carregar os preços atuais.'
  if (historyResult.status === 'fulfilled') {
    history.value = historyResult.value
    setPeriodDates()
  } else {
    historyError.value =
      historyResult.reason instanceof Error
        ? historyResult.reason.message
        : 'Não foi possível carregar o histórico.'
  }
  if (storesResult.status === 'fulfilled') supermarkets.value = storesResult.value
  else if (comparison.value)
    supermarkets.value = comparison.value.precos.map((price) => price.supermercado)
  loading.value = false
  imageFailed.value = false
}

async function returnToResults() {
  await router.push({ name: 'home' })
}

watch(
  () => route.params.id,
  () => void loadProduct(),
)
onMounted(() => void loadProduct())
</script>

<template>
  <div class="mvp-app pd-page">
    <main class="pd-main">
      <div class="pd-back-row">
        <button type="button" @click="returnToResults">
          <span aria-hidden="true">←</span> Voltar para os resultados da busca</button
        ><span v-if="isDemoData" class="pd-demo-tag">Dados demonstrativos</span>
      </div>
      <p v-if="loading" class="pd-state">Carregando produto e histórico…</p>
      <div v-else-if="productError" class="pd-error" role="alert">{{ productError }}</div>
      <template v-else-if="product">
        <section class="pd-intro">
          <div class="pd-intro-copy">
            <p class="mvp-eyebrow">DETALHES DO PRODUTO</p>
            <h1>Histórico de preços</h1>
            <p>Veja a evolução dos preços deste produto nas coletas registradas.</p>
          </div>
          <article class="pd-product-card">
            <div class="pd-product-image">
              <img
                v-if="productImage"
                :src="productImage"
                :alt="productName"
                @error="handleImageError"
              />
              <div v-else class="pd-image-fallback" aria-hidden="true">
                <strong>{{ productName }}</strong
                ><small>Imagem indisponível</small>
              </div>
            </div>
            <div class="pd-product-info">
              <h2>{{ productName }}</h2>
              <p>{{ productBrand }}</p>
              <small>Comparação entre supermercados de Ribeirão Preto</small>
            </div>
            <button class="pd-add-button" type="button" @click="addToBasket(product!)">
              <span aria-hidden="true">＋</span> Adicionar à lista
            </button>
          </article>
        </section>

        <section class="pd-current" aria-labelledby="current-prices-title">
          <div class="pd-section-heading">
            <h2 id="current-prices-title">Preços mais recentes</h2>
            <span>Por supermercado</span>
          </div>
          <p v-if="comparisonError" class="pd-inline-error" role="alert">{{ comparisonError }}</p>
          <div v-else-if="currentPrices.length" class="pd-current-grid">
            <article
              v-for="(price, index) in currentPrices"
              :key="price.supermercado.id"
              class="pd-current-store"
              :class="{ unavailable: !price.disponivel }"
            >
              <span
                class="pd-store-dot"
                :style="{ '--store-color': storeColors[index % storeColors.length] }"
              ></span>
              <div>
                <strong>{{ price.supermercado.nome }}</strong
                ><small v-if="price.disponivel && price.data_hora_coleta"
                  >Atualizado {{ formatDate(price.data_hora_coleta) }}</small
                ><small v-else>Sem preço disponível</small>
              </div>
              <strong class="pd-current-price">{{
                price.disponivel ? formatPrice(price.valor!) : 'Indisponível'
              }}</strong>
              <a
                v-if="price.disponivel && price.url_fonte"
                :href="price.url_fonte"
                target="_blank"
                rel="noopener noreferrer"
                >Fonte ↗</a
              >
            </article>
          </div>
          <p v-else class="pd-muted">Não há preços recentes para exibir.</p>
        </section>

        <section class="pd-filterbar" aria-label="Filtros do histórico">
          <div class="pd-filter-title">
            <span aria-hidden="true">▽</span><strong>Filtrar histórico</strong>
          </div>
          <label
            ><span>Supermercado</span
            ><select v-model="selectedSupermarket" @change="loadHistory">
              <option value="">Todos os supermercados</option>
              <option v-for="store in supermarkets" :key="store.id" :value="String(store.id)">
                {{ store.nome }}
              </option>
            </select></label
          >
          <label
            ><span>Período</span
            ><select v-model="period" @change="setPeriodDates">
              <option value="1m">Último mês</option>
              <option value="3m">Últimos 3 meses</option>
              <option value="6m">Últimos 6 meses</option>
              <option value="all">Todo o histórico</option>
            </select></label
          >
          <label><span>Data inicial</span><input v-model="startDate" type="date" /></label>
          <label><span>Data final</span><input v-model="endDate" type="date" /></label>
          <button class="pd-filter-button" type="button" @click="applyFilters">
            <span aria-hidden="true">⌕</span> Filtrar
          </button>
        </section>

        <p v-if="historyError" class="pd-inline-error" role="alert">{{ historyError }}</p>
        <p v-if="loadingHistory" class="pd-state">Atualizando histórico…</p>
        <div v-else-if="!historyError" class="pd-analysis-grid" id="historico">
          <section class="pd-chart-panel" aria-labelledby="chart-title">
            <div class="pd-section-heading">
              <h2 id="chart-title"><span aria-hidden="true">↗</span> Evolução do preço</h2>
              <span>{{ historyRecords.length }} registros</span>
            </div>
            <div v-if="historyChart" class="pd-chart-scroll">
              <svg
                class="pd-chart"
                viewBox="0 0 760 220"
                role="img"
                :aria-label="`Histórico de preços de ${productName}`"
              >
                <g v-for="tick in historyChart.priceTicks" :key="tick.y">
                  <line x1="54" x2="738" :y1="tick.y" :y2="tick.y" />
                  <text x="46" :y="tick.y + 4" text-anchor="end">
                    {{ formatPrice(tick.value) }}
                  </text>
                </g>
                <g v-for="tick in historyChart.dateTicks" :key="tick.date">
                  <text :x="tick.x" y="198" text-anchor="middle">{{ tick.label }}</text>
                </g>
                <g v-for="series in historyChart.series" :key="series.id">
                  <polyline
                    v-if="series.points.length > 1"
                    :points="series.points.map((point) => `${point.x},${point.y}`).join(' ')"
                    :stroke="series.color"
                  />
                  <circle
                    v-for="(point, index) in series.points"
                    :key="`${series.id}-${index}`"
                    :cx="point.x"
                    :cy="point.y"
                    r="4"
                    :fill="series.color"
                  >
                    <title>
                      {{ series.name }} · {{ formatDate(point.entry.data_hora_coleta) }} ·
                      {{ formatPrice(point.entry.valor) }}
                    </title>
                  </circle>
                </g>
              </svg>
            </div>
            <p v-else class="pd-chart-empty">
              Ainda não há registros suficientes para montar o gráfico.
            </p>
            <ul v-if="historyChart" class="pd-legend">
              <li v-for="series in historyChart.series" :key="series.id">
                <span :style="{ '--store-color': series.color }"></span>{{ series.name }}
              </li>
            </ul>
          </section>
          <aside class="pd-summary-panel" aria-labelledby="summary-title">
            <div class="pd-section-heading">
              <h2 id="summary-title"><span aria-hidden="true">▥</span> Resumo do período</h2>
            </div>
            <div v-if="historySummary" class="pd-summary-values">
              <div>
                <span>Menor preço</span
                ><strong class="lowest">{{ formatPrice(historySummary.cheapest.valor) }}</strong
                ><small>{{ formatDay(historySummary.cheapest.data_hora_coleta) }}</small>
              </div>
              <div>
                <span>Maior preço</span
                ><strong class="highest">{{
                  formatPrice(historySummary.mostExpensive.valor)
                }}</strong
                ><small>{{ formatDay(historySummary.mostExpensive.data_hora_coleta) }}</small>
              </div>
              <div>
                <span>Preço médio</span><strong>{{ formatPrice(historySummary.average) }}</strong
                ><small>{{ historySummary.count }} registros</small>
              </div>
            </div>
            <p v-else class="pd-chart-empty">Sem dados no período selecionado.</p>
          </aside>
        </div>

        <section class="pd-records" aria-labelledby="records-title">
          <div class="pd-section-heading">
            <h2 id="records-title">
              <span aria-hidden="true">◷</span> Registros de preços
              <span class="pd-record-count">({{ historyRecords.length }} resultados)</span>
            </h2>
            <label class="pd-sort"
              ><span>Ordenar por</span
              ><select aria-label="Ordenar registros" disabled>
                <option>Data (mais antigos primeiro)</option>
              </select></label
            >
          </div>
          <p v-if="loadingHistory" class="pd-state">Carregando registros…</p>
          <p v-else-if="historyError" class="pd-inline-error">{{ historyError }}</p>
          <div v-else-if="historyRecords.length" class="pd-table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Data e hora da coleta</th>
                  <th>Supermercado</th>
                  <th>Preço</th>
                  <th>Fonte</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(entry, index) in historyRecords"
                  :key="`${entry.supermercado.id}-${entry.data_hora_coleta}-${index}`"
                >
                  <td>
                    <time :datetime="entry.data_hora_coleta">{{
                      formatDate(entry.data_hora_coleta)
                    }}</time>
                  </td>
                  <td>
                    <span class="pd-table-store"
                      ><i :style="{ '--store-color': storeColors[index % storeColors.length] }"></i
                      >{{ entry.supermercado.nome }}</span
                    >
                  </td>
                  <td class="pd-table-price">{{ formatPrice(entry.valor) }}</td>
                  <td>
                    <a :href="entry.url_fonte" target="_blank" rel="noopener noreferrer"
                      >↗ <span>Ver no site</span></a
                    >
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="pd-empty">
            Nenhum registro de preço disponível para os filtros selecionados.
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.pd-main {
  padding: 20px 0 42px;
}
.pd-back-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 17px;
}
.pd-back-row button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border: 0;
  background: transparent;
  color: #347150;
  font-size: 11px;
  font-weight: 600;
}
.pd-back-row button span {
  font-size: 18px;
}
.pd-demo-tag {
  color: #8b7752;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}
.pd-intro {
  display: grid;
  grid-template-columns: minmax(260px, 0.8fr) minmax(0, 1.7fr);
  align-items: center;
  gap: 22px;
  margin-bottom: 17px;
}
.pd-intro-copy h1 {
  margin: 0;
  color: #202c25;
  font-size: 27px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: 0;
}
.pd-intro-copy p:last-child {
  max-width: 390px;
  margin: 8px 0 0;
  color: #78837b;
  font-size: 10px;
  line-height: 1.5;
}
.pd-product-card {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  min-height: 112px;
  padding: 10px 16px 10px 10px;
  border: 1px solid #e3eae4;
  border-radius: 7px;
  background: #fff;
}
.pd-product-image {
  display: grid;
  place-items: center;
  width: 112px;
  height: 90px;
  overflow: hidden;
  background: #fbfcfa;
}
.pd-product-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.pd-image-fallback {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px;
  background: #edf4ee;
  color: #41624d;
  text-align: center;
}
.pd-image-fallback strong {
  font-size: 9px;
  line-height: 1.4;
}
.pd-image-fallback small {
  color: #818d84;
  font-size: 7px;
}
.pd-product-info {
  min-width: 0;
}
.pd-product-info h2 {
  margin: 0;
  color: #28342c;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
.pd-product-info p {
  margin: 4px 0 0;
  color: #58665d;
  font-size: 11px;
  font-weight: 600;
}
.pd-product-info small {
  display: block;
  margin-top: 5px;
  color: #89948c;
  font-size: 9px;
}
.pd-add-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 11px;
  border: 1px solid #dce7dd;
  border-radius: 4px;
  background: #f4f8f4;
  color: #356b4b;
  font-size: 9px;
  font-weight: 700;
  white-space: nowrap;
}
.pd-add-button span {
  font-size: 15px;
}
.pd-current {
  margin: 16px 0;
  padding: 12px 14px;
  border: 1px solid #e3eae4;
  border-radius: 6px;
  background: #fff;
}
.pd-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.pd-section-heading h2 {
  margin: 0;
  color: #334138;
  font-size: 12px;
  font-weight: 700;
}
.pd-section-heading h2 > span {
  margin-right: 5px;
  color: #338157;
}
.pd-section-heading > span {
  color: #8b958e;
  font-size: 9px;
}
.pd-current-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
  margin-top: 10px;
}
.pd-current-store {
  display: grid;
  grid-template-columns: 9px minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px 8px;
  min-width: 0;
  padding: 9px;
  border: 1px solid #e8ede8;
  border-radius: 4px;
}
.pd-store-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--store-color);
}
.pd-current-store > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}
.pd-current-store > div strong {
  overflow: hidden;
  color: #3f4b42;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pd-current-store small {
  color: #929b94;
  font-size: 7px;
}
.pd-current-price {
  color: #1e7648;
  font-size: 11px;
  white-space: nowrap;
}
.pd-current-store.unavailable .pd-current-price {
  color: #929b94;
  font-size: 8px;
  font-weight: 500;
}
.pd-current-store a {
  grid-column: 2 / -1;
  justify-self: start;
  color: #317a4d;
  font-size: 8px;
}
.pd-muted {
  margin: 10px 0 0;
  color: #8c968e;
  font-size: 9px;
}
.pd-inline-error {
  margin: 10px 0;
  color: #974c3d;
  font-size: 10px;
}
.pd-filterbar {
  display: grid;
  grid-template-columns: 145px repeat(4, minmax(110px, 1fr)) 82px;
  align-items: end;
  gap: 11px;
  margin: 16px 0 13px;
  padding: 13px 15px;
  border-radius: 7px;
  background: #e8f5ee;
}
.pd-filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  color: #37463c;
  font-size: 10px;
}
.pd-filter-title span {
  color: #16824d;
  font-size: 15px;
}
.pd-filterbar label {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
}
.pd-filterbar label > span {
  color: #526157;
  font-size: 8px;
  font-weight: 600;
}
.pd-filterbar select,
.pd-filterbar input {
  width: 100%;
  min-width: 0;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #e1e8e1;
  border-radius: 4px;
  background: #fff;
  color: #47544b;
  font: inherit;
  font-size: 9px;
}
.pd-filter-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 32px;
  border: 0;
  border-radius: 4px;
  background: #128b51;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
}
.pd-analysis-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(250px, 0.92fr);
  gap: 12px;
  margin-bottom: 13px;
}
.pd-chart-panel,
.pd-summary-panel,
.pd-records {
  min-width: 0;
  border: 1px solid #e5ebe5;
  border-radius: 7px;
  background: #fff;
}
.pd-chart-panel {
  padding: 12px 13px 9px;
}
.pd-chart-scroll {
  width: 100%;
  overflow-x: auto;
}
.pd-chart {
  display: block;
  width: 100%;
  min-width: 520px;
  height: auto;
  overflow: visible;
}
.pd-chart line {
  stroke: #e9eeea;
  stroke-width: 1;
}
.pd-chart text {
  fill: #818c84;
  font-family: 'DM Sans', sans-serif;
  font-size: 10px;
}
.pd-chart polyline {
  fill: none;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.pd-chart circle {
  stroke: #fff;
  stroke-width: 1.5;
}
.pd-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 2px 0 0;
  padding: 0;
  list-style: none;
}
.pd-legend li {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #758078;
  font-size: 8px;
}
.pd-legend li span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--store-color);
}
.pd-chart-empty {
  display: grid;
  min-height: 170px;
  place-items: center;
  color: #8c968e;
  font-size: 10px;
  text-align: center;
}
.pd-summary-panel {
  padding: 12px 13px;
  background: #eaf5ee;
}
.pd-summary-values {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 19px;
}
.pd-summary-values > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}
.pd-summary-values span {
  color: #718076;
  font-size: 8px;
}
.pd-summary-values strong {
  color: #26362b;
  font-size: 12px;
  white-space: nowrap;
}
.pd-summary-values strong.lowest {
  color: #17834d;
}
.pd-summary-values strong.highest {
  color: #c84f57;
}
.pd-summary-values small {
  color: #87928a;
  font-size: 7px;
}
.pd-records {
  overflow: hidden;
}
.pd-records > .pd-section-heading {
  min-height: 43px;
  padding: 0 13px;
  border-bottom: 1px solid #e6ebe6;
}
.pd-record-count {
  color: #87928a;
  font-size: 9px;
  font-weight: 400;
}
.pd-sort {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7e8981;
  font-size: 8px;
}
.pd-sort select {
  height: 27px;
  max-width: 180px;
  padding: 0 7px;
  border: 1px solid #e3e9e3;
  border-radius: 4px;
  background: #fff;
  color: #4f5b52;
  font-size: 8px;
}
.pd-table-scroll {
  width: 100%;
  overflow-x: auto;
}
.pd-records table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
.pd-records th {
  height: 29px;
  padding: 0 12px;
  background: #f5f7f5;
  color: #46534a;
  font-size: 8px;
  font-weight: 700;
}
.pd-records td {
  height: 29px;
  padding: 0 12px;
  border-bottom: 1px solid #edf0ed;
  color: #67736a;
  font-size: 8px;
  white-space: nowrap;
}
.pd-table-store {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.pd-table-store i {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  background: var(--store-color);
}
.pd-table-price {
  color: #3c4940 !important;
  font-weight: 700;
}
.pd-records td a {
  color: #3276a7;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.pd-records td a span {
  margin-left: 3px;
}
.pd-empty,
.pd-state,
.pd-error {
  padding: 22px 12px;
  color: #7e8981;
  font-size: 10px;
  text-align: center;
}
.pd-error {
  color: #974c3d;
}
@media (max-width: 1050px) {
  .pd-filterbar {
    grid-template-columns: 1fr 1fr 1fr;
  }
  .pd-filter-title {
    grid-column: 1 / -1;
    height: auto;
  }
  .pd-filter-button {
    min-height: 32px;
  }
  .pd-intro {
    grid-template-columns: minmax(190px, 0.7fr) minmax(0, 1.3fr);
  }
}
@media (max-width: 760px) {
  .pd-main {
    padding-top: 15px;
  }
  .pd-intro {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .pd-intro-copy h1 {
    font-size: 24px;
  }
  .pd-product-card {
    grid-template-columns: 78px minmax(0, 1fr);
    gap: 10px;
    padding: 8px;
  }
  .pd-product-image {
    width: 78px;
    height: 76px;
  }
  .pd-product-info h2 {
    font-size: 12px;
  }
  .pd-product-info small {
    font-size: 8px;
  }
  .pd-add-button {
    grid-column: 1 / -1;
    width: 100%;
  }
  .pd-current-grid {
    grid-template-columns: 1fr;
  }
  .pd-current-store {
    grid-template-columns: 9px minmax(0, 1fr) auto;
  }
  .pd-filterbar {
    grid-template-columns: 1fr 1fr;
    gap: 9px;
    padding: 11px;
  }
  .pd-filter-title {
    grid-column: 1 / -1;
  }
  .pd-analysis-grid {
    grid-template-columns: 1fr;
  }
  .pd-summary-panel {
    grid-row: 1;
  }
  .pd-summary-values {
    margin-top: 12px;
  }
  .pd-summary-values strong {
    font-size: 11px;
  }
  .pd-chart-panel {
    grid-row: 2;
  }
  .pd-chart {
    min-width: 570px;
  }
  .pd-records > .pd-section-heading {
    align-items: start;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    padding: 9px 12px;
  }
  .pd-sort {
    width: 100%;
    justify-content: space-between;
  }
  .pd-records table {
    min-width: 620px;
  }
}
@media (max-width: 440px) {
  .pd-demo-tag {
    font-size: 7px;
  }
  .pd-filterbar {
    grid-template-columns: 1fr;
  }
  .pd-filter-title {
    grid-column: 1;
  }
  .pd-filterbar label > span {
    font-size: 9px;
  }
  .pd-summary-values {
    gap: 5px;
  }
  .pd-summary-values span {
    font-size: 7px;
  }
  .pd-summary-values strong {
    font-size: 10px;
  }
}
</style>
