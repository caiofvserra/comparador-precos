<script setup lang="ts">
import { computed, ref } from 'vue'
import { productImageUrl } from '../composables/useShoppingList'
import type { Product, Simulation, SupermarketResult } from '../services/api'

const props = withDefaults(
  defineProps<{
    simulation: Simulation | null
    products: Product[]
    itemCount: number
    loading?: boolean
    error?: string
    compact?: boolean
    showHeading?: boolean
    comparisonMode?: boolean
  }>(),
  { loading: false, error: '', compact: false, showHeading: true, comparisonMode: false },
)

const emit = defineEmits<{ calculate: []; editList: []; browseProducts: [] }>()
const orderBy = ref('total')
const selectedMarketId = ref<number | null>(null)
const failedLogos = ref<string[]>([])
const failedProductImages = ref<number[]>([])

const orderedMarkets = computed(() => {
  const results = [...(props.simulation?.supermercados ?? [])]
  return results.sort((first, second) => {
    if (orderBy.value === 'market')
      return first.supermercado.nome.localeCompare(second.supermercado.nome, 'pt-BR')
    if (first.status !== second.status) return first.status === 'completo' ? -1 : 1
    return Number(first.total) - Number(second.total)
  })
})

const completeMarkets = computed(() =>
  (props.simulation?.supermercados ?? [])
    .filter((market) => market.status === 'completo')
    .filter((market) => Number.isFinite(Number(market.total)) && Number(market.total) >= 0)
    .sort((first, second) => Number(first.total) - Number(second.total)),
)

const cheapestCompleteTotal = computed(() => {
  if (!completeMarkets.value.length) return null
  return Number(completeMarkets.value[0]!.total)
})

const cheapestMarket = computed(() => completeMarkets.value[0] ?? null)
const nextDistinctPriceMarket = computed(() => {
  if (cheapestCompleteTotal.value === null) return null
  return completeMarkets.value.find((market) => Number(market.total) > cheapestCompleteTotal.value!) ?? null
})
const savingsOpportunity = computed(() => {
  if (!cheapestMarket.value || !nextDistinctPriceMarket.value) return null
  const amount = Number(nextDistinctPriceMarket.value.total) - Number(cheapestMarket.value.total)
  if (!(amount > 0)) return null
  return {
    amount,
    percentage: Number(cheapestMarket.value.total) > 0
      ? (amount / Number(cheapestMarket.value.total)) * 100
      : null,
  }
})
const selectedDetailMarket = computed(() => {
  const selected = orderedMarkets.value.find(
    (market) => market.supermercado.id === selectedMarketId.value,
  )
  return selected ?? cheapestMarket.value ?? orderedMarkets.value[0] ?? null
})

function isCheapestMarket(result: SupermarketResult) {
  return (
    result.status === 'completo' &&
    cheapestCompleteTotal.value !== null &&
    Number(result.total) === cheapestCompleteTotal.value
  )
}

function totalDifference(result: SupermarketResult) {
  if (result.status !== 'completo' || cheapestCompleteTotal.value === null) return null

  const total = Number(result.total)
  const difference = total - cheapestCompleteTotal.value
  return {
    amount: difference,
    percentage: cheapestCompleteTotal.value > 0
      ? (difference / cheapestCompleteTotal.value) * 100
      : null,
  }
}

function formatPrice(value: string | number) {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function productName(productId: number) {
  return props.products.find((product) => product.id === productId)?.nome || `Produto ${productId}`
}

function productImage(productId: number) {
  const product = props.products.find((entry) => entry.id === productId)
  return product ? productImageUrl(product) : ''
}

function productImageFailed(productId: number) {
  return failedProductImages.value.includes(productId)
}

function onProductImageError(productId: number) {
  if (!failedProductImages.value.includes(productId)) failedProductImages.value.push(productId)
}

function coverage(result: SupermarketResult) {
  const total = props.simulation?.total_itens ?? 0
  return `${result.itens_encontrados} de ${total} ${total === 1 ? 'item encontrado' : 'itens encontrados'}`
}

function marketLogoUrl(name: string) {
  const normalized = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR')
  const baseUrl = import.meta.env.BASE_URL
  if (normalized.includes('atacadao')) return `${baseUrl}logos/atacadao.svg`
  if (normalized.includes('savegnago')) return `${baseUrl}logos/savegnago.svg`
  if (normalized.includes('carrefour')) return `${baseUrl}logos/carrefour.svg`
  return ''
}

function logoFailed(name: string) {
  return failedLogos.value.includes(name)
}

function onLogoError(name: string) {
  if (!failedLogos.value.includes(name)) failedLogos.value.push(name)
}

function selectMarket(marketId: number) {
  selectedMarketId.value = marketId
}
</script>
<template>
  <section
    class="shopping-totals"
    :class="{ compact, 'comparison-mode': comparisonMode }"
    aria-labelledby="shopping-totals-title"
  >
    <template v-if="comparisonMode">
      <div v-if="simulation" class="comparison-controls">
        <span><span class="sort-symbol" aria-hidden="true">☷</span> Ordenar por</span>
        <label class="comparison-sort-select">
          <span class="visually-hidden">Ordenar supermercados</span>
          <select v-model="orderBy">
            <option value="total">Menor preço total</option>
            <option value="market">Nome do mercado</option>
          </select>
        </label>
      </div>

      <p v-if="error" class="totals-error" role="alert">{{ error }}</p>

      <div v-if="!simulation" class="totals-empty comparison-empty">
        <span class="comparison-empty-icon" aria-hidden="true">▥</span>
        <div class="comparison-empty-copy">
          <strong>{{ itemCount ? 'Sua lista está pronta para comparar' : 'Sua lista ainda está vazia' }}</strong>
          <p>{{ itemCount ? 'Calcule os totais para comparar os supermercados disponíveis.' : 'Adicione produtos à lista para descobrir onde sua compra pode sair mais em conta.' }}</p>
        </div>
        <button
          v-if="itemCount"
          class="comparison-empty-action"
          type="button"
          :disabled="loading"
          @click="emit('calculate')"
        >{{ loading ? 'Calculando…' : 'Comparar preços' }}</button>
        <button
          v-else
          class="comparison-empty-action"
          type="button"
          @click="emit('browseProducts')"
        >Buscar produtos</button>
      </div>

      <template v-else>
        <div class="market-grid comparison-market-grid">
          <article
            v-for="result in orderedMarkets"
            :key="result.supermercado.id"
            class="market-card comparison-market-card"
            :class="[
              { incomplete: result.status === 'incompleto' },
              { cheapest: isCheapestMarket(result) },
              { selected: selectedDetailMarket?.supermercado.id === result.supermercado.id },
            ]"
          >
            <div class="comparison-card-heading">
              <div class="market-logo comparison-market-logo" :class="`market-logo-${result.supermercado.id}`">
                <img
                  v-if="marketLogoUrl(result.supermercado.nome) && !logoFailed(result.supermercado.nome)"
                  :src="marketLogoUrl(result.supermercado.nome)"
                  :alt="`Logo ${result.supermercado.nome}`"
                  @error="onLogoError(result.supermercado.nome)"
                />
                <span v-else aria-hidden="true">{{ result.supermercado.nome.slice(0, 1) }}</span>
              </div>
              <div class="market-ident comparison-market-ident">
                <strong>{{ result.supermercado.nome }}</strong>
                <small>
                  <span class="coverage-indicator" :class="result.status" aria-hidden="true">{{ result.status === 'completo' ? '✓' : '!' }}</span>
                  {{ coverage(result) }}
                </small>
              </div>
              <span v-if="isCheapestMarket(result)" class="comparison-winner-pill">Melhor preço</span>
            </div>

            <div class="market-card-total comparison-total">
              <span>{{ result.status === 'completo' ? 'Valor total estimado' : `Total parcial · ${result.itens_encontrados} itens` }}</span>
              <strong>{{ formatPrice(result.total) }}</strong>
            </div>

            <p v-if="isCheapestMarket(result)" class="market-best-label comparison-best-label">
              <span aria-hidden="true">♛</span> Menor total para a lista
            </p>
            <p v-else-if="totalDifference(result)" class="market-total-difference comparison-difference">
              <span aria-hidden="true">↗</span>
              <span>
                <strong>+ {{ formatPrice(totalDifference(result)!.amount) }}<template v-if="totalDifference(result)!.percentage !== null"> ({{ totalDifference(result)!.percentage!.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}%)</template></strong>
                <small>a mais que o menor total</small>
              </span>
            </p>
            <p v-else-if="result.status === 'incompleto'" class="comparison-incomplete-note">
              Faltam {{ result.itens_ausentes.length }} {{ result.itens_ausentes.length === 1 ? 'produto' : 'produtos' }} nesta loja.
            </p>
            <p v-else class="comparison-equal-note">Mesmo menor total</p>

            <button
              class="comparison-details-button"
              :class="{ primary: isCheapestMarket(result), active: selectedDetailMarket?.supermercado.id === result.supermercado.id }"
              type="button"
              :aria-pressed="selectedDetailMarket?.supermercado.id === result.supermercado.id"
              @click="selectMarket(result.supermercado.id)"
            >Ver detalhes <span aria-hidden="true">→</span></button>
          </article>
        </div>

        <div v-if="selectedDetailMarket" class="comparison-detail-grid">
          <section class="comparison-breakdown" aria-label="Detalhes dos produtos por supermercado">
            <header class="comparison-breakdown-heading">
              <div class="comparison-detail-market">
                <div class="comparison-detail-logo">
                  <img
                    v-if="marketLogoUrl(selectedDetailMarket.supermercado.nome) && !logoFailed(selectedDetailMarket.supermercado.nome)"
                    :src="marketLogoUrl(selectedDetailMarket.supermercado.nome)"
                    :alt="`Logo ${selectedDetailMarket.supermercado.nome}`"
                    @error="onLogoError(selectedDetailMarket.supermercado.nome)"
                  />
                  <span v-else aria-hidden="true">{{ selectedDetailMarket.supermercado.nome.slice(0, 1) }}</span>
                </div>
                <div>
                  <h3>{{ selectedDetailMarket.supermercado.nome }}</h3>
                  <p>{{ coverage(selectedDetailMarket) }}</p>
                </div>
                <span v-if="isCheapestMarket(selectedDetailMarket)" class="comparison-detail-cheapest">Menor total</span>
              </div>
              <div class="comparison-detail-total">
                <span>{{ selectedDetailMarket.status === 'completo' ? 'Valor total estimado' : 'Total parcial estimado' }}</span>
                <strong>{{ formatPrice(selectedDetailMarket.total) }}</strong>
              </div>
            </header>

            <div class="comparison-table-scroll">
              <table class="comparison-products-table">
                <thead>
                  <tr><th>Produto</th><th>Quantidade</th><th>Preço unitário</th><th>Subtotal</th></tr>
                </thead>
                <tbody>
                  <tr v-for="item in selectedDetailMarket.itens" :key="item.produto_id">
                    <td>
                      <span class="comparison-product-cell">
                        <img
                          v-if="productImage(item.produto_id) && !productImageFailed(item.produto_id)"
                          :src="productImage(item.produto_id)"
                          alt=""
                          loading="lazy"
                          @error="onProductImageError(item.produto_id)"
                        />
                        <span class="comparison-product-name">{{ productName(item.produto_id) }}</span>
                      </span>
                    </td>
                    <td>{{ item.quantidade }} un.</td>
                    <td>{{ formatPrice(item.valor_unitario) }}</td>
                    <td class="comparison-subtotal">{{ formatPrice(item.subtotal) }}</td>
                  </tr>
                  <tr v-for="productId in selectedDetailMarket.itens_ausentes" :key="productId" class="comparison-product-missing">
                    <td>{{ productName(productId) }}</td><td>—</td><td>—</td><td>Não encontrado</td>
                  </tr>
                  <tr v-if="!selectedDetailMarket.itens.length && !selectedDetailMarket.itens_ausentes.length">
                    <td colspan="4" class="comparison-no-products">Nenhum produto disponível para detalhar.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <aside class="comparison-insights" aria-label="Resumo e economia">
            <section class="comparison-insight-card savings-tip">
              <div class="comparison-insight-icon" aria-hidden="true">♧</div>
              <div>
                <h3>Dica de economia</h3>
                <p v-if="cheapestMarket && savingsOpportunity">
                  <strong>{{ cheapestMarket.supermercado.nome }}</strong> tem o menor total para sua lista. Comparando com {{ nextDistinctPriceMarket?.supermercado.nome }}, você pode economizar <strong>{{ formatPrice(savingsOpportunity.amount) }}</strong><template v-if="savingsOpportunity.percentage !== null"> ({{ savingsOpportunity.percentage.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}%)</template>.
                </p>
                <p v-else-if="cheapestMarket && completeMarkets.length > 1">
                  {{ cheapestMarket.supermercado.nome }} divide o menor total com outro supermercado. Não há diferença de preço positiva para destacar entre as opções completas mais baratas.
                </p>
                <p v-else-if="cheapestMarket">
                  {{ cheapestMarket.supermercado.nome }} tem o menor total entre as opções completas. Não há outro supermercado com a lista completa para calcular uma economia comparativa.
                </p>
                <p v-else>
                  Nenhum supermercado encontrou todos os produtos da lista. Confira os itens ausentes antes de comparar os totais parciais.
                </p>
              </div>
            </section>

            <section class="comparison-insight-card list-summary">
              <div class="list-summary-title"><span aria-hidden="true">▤</span><h3>Resumo da sua lista</h3></div>
              <div class="list-summary-line"><span>Produtos na simulação</span><strong>{{ simulation.total_itens }}</strong></div>
              <div class="list-summary-line"><span>Supermercados</span><strong>{{ simulation.supermercados.length }}</strong></div>
              <div class="list-summary-line summary-total"><span>Total da lista (menor valor)</span><strong>{{ cheapestMarket ? formatPrice(cheapestMarket.total) : '—' }}</strong></div>
              <button class="comparison-edit-list" type="button" @click="emit('editList')">Editar minha lista <span aria-hidden="true">→</span></button>
            </section>
          </aside>
        </div>
      </template>

    </template>

    <template v-else>
      <header v-if="showHeading" class="totals-heading">
        <div>
          <p v-if="!compact" class="totals-kicker">COMPARAÇÃO DA LISTA</p>
          <h2 id="shopping-totals-title">Totais por supermercado</h2>
          <p v-if="!compact" class="totals-description">
            Totais oficiais calculados com o preço coletado mais recente de cada item.
          </p>
        </div>
        <label v-if="simulation && !compact" class="totals-sort">
          <span>Ordenar por</span>
          <select v-model="orderBy">
            <option value="total">Menor total completo</option>
            <option value="market">Nome do mercado</option>
          </select>
        </label>
      </header>

      <p v-if="error" class="totals-error" role="alert">{{ error }}</p>
      <div v-if="!simulation" class="totals-empty">
        <span aria-hidden="true">▥</span>
        <p>{{ itemCount ? 'Calcule sua lista para comparar os mercados.' : 'Adicione produtos antes de calcular os totais.' }}</p>
      </div>
      <div v-else class="market-grid">
        <article
          v-for="result in orderedMarkets"
          :key="result.supermercado.id"
          class="market-card"
          :class="[
            { incomplete: result.status === 'incompleto' },
            { cheapest: isCheapestMarket(result) },
          ]"
        >
          <header class="market-card-header">
            <span class="market-logo" :class="`market-logo-${result.supermercado.id}`">
              <img
                v-if="marketLogoUrl(result.supermercado.nome) && !logoFailed(result.supermercado.nome)"
                :src="marketLogoUrl(result.supermercado.nome)"
                :alt="`Logo ${result.supermercado.nome}`"
                @error="onLogoError(result.supermercado.nome)"
              />
              <span v-else aria-hidden="true">{{ result.supermercado.nome.slice(0, 1) }}</span>
            </span>
            <div class="market-ident">
              <strong>{{ result.supermercado.nome }}</strong><small>{{ coverage(result) }}</small>
            </div>
            <span class="market-status" :class="result.status">
              <i aria-hidden="true">{{ result.status === 'completo' ? '✓' : '!' }}</i>{{ result.status === 'completo' ? 'Lista completa' : 'Lista incompleta' }}
            </span>
          </header>
          <div class="market-card-total">
            <span>{{ result.status === 'completo' ? 'Valor total estimado' : `Total estimado (${result.itens_encontrados} itens)` }}</span>
            <strong>{{ formatPrice(result.total) }}</strong>
          </div>
          <p v-if="isCheapestMarket(result)" class="market-best-label">✓ Menor total para a lista</p>
          <p v-else-if="totalDifference(result)" class="market-total-difference">
            + {{ formatPrice(totalDifference(result)!.amount) }}
            <template v-if="totalDifference(result)!.percentage !== null">
              ({{ totalDifference(result)!.percentage!.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}%)
            </template>
            a mais que o menor total
          </p>
          <div class="market-items-table">
            <div class="market-items-head"><span>Produto</span><span>Qtd.</span><span>Valor unitário</span><span>Subtotal</span></div>
            <div v-for="item in result.itens" :key="item.produto_id" class="market-item-line">
              <span class="market-item-name">{{ productName(item.produto_id) }}</span>
              <span>{{ item.quantidade }}</span><span>{{ formatPrice(item.valor_unitario) }}</span><strong>{{ formatPrice(item.subtotal) }}</strong>
            </div>
            <div v-for="productId in result.itens_ausentes" :key="productId" class="market-item-line missing">
              <span class="market-item-name">{{ productName(productId) }}</span><span>—</span><span>—</span><strong>Não encontrado</strong>
            </div>
          </div>
          <footer class="market-card-footer"><span>{{ result.status === 'completo' ? 'Total estimado' : 'Total parcial' }}</span><strong>{{ formatPrice(result.total) }}</strong></footer>
        </article>
      </div>
      <button
        class="calculate-list-button"
        type="button"
        :disabled="itemCount === 0 || loading"
        @click="emit('calculate')"
      ><span aria-hidden="true">{{ loading ? '◌' : '▥' }}</span>{{ loading ? 'Calculando totais…' : 'Calcular totais por supermercado' }}</button>
    </template>
  </section>
</template>
<style scoped>
.shopping-totals {
  min-width: 0;
}
.totals-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 13px;
}
.totals-kicker {
  margin: 0 0 4px;
  color: #708878;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.8px;
}
.totals-heading h2 {
  margin: 0;
  color: #27362d;
  font-size: 18px;
  font-weight: 700;
}
.totals-description {
  margin: 5px 0 0;
  color: #818c84;
  font-size: 9px;
}
.totals-sort {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #748077;
  font-size: 9px;
}
.totals-sort select {
  height: 29px;
  padding: 0 8px;
  border: 1px solid #e1e8e1;
  border-radius: 4px;
  background: #fff;
  color: #46534a;
  font-size: 9px;
}
.market-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: stretch;
  gap: 10px;
}
.market-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 11px 10px 9px;
  border: 1px solid #e3e9e3;
  border-radius: 7px;
  background: #fff;
}
.market-card-header {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
}
.market-logo {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #e8f1e8;
  color: #2b7047;
  font-size: 12px;
  font-weight: 800;
}
.market-logo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.market-logo > span {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
}
.market-logo-2 {
  background: #fff0dd;
  color: #a96922;
}
.market-logo-3 {
  background: #fce8e8;
  color: #b33e43;
}
.market-ident {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}
.market-ident strong {
  overflow: hidden;
  color: #334037;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.market-ident small {
  color: #818c84;
  font-size: 7px;
  line-height: 1.3;
}
.market-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  padding: 4px 6px;
  border-radius: 20px;
  background: #e3f4e8;
  color: #27814a;
  font-size: 7px;
  font-weight: 700;
  white-space: nowrap;
}
.market-status i {
  font-size: 8px;
  font-style: normal;
}
.market-status.incompleto {
  background: #fff0d5;
  color: #986711;
}
.market-card-total {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin: 13px 0 8px;
}
.market-card-total span {
  color: #68746b;
  font-size: 8px;
}
.market-card-total strong {
  color: #21834a;
  font-size: 18px;
  line-height: 1.15;
}
.market-card.incomplete .market-card-total strong {
  color: #9b7025;
}
.market-items-table {
  flex: 1;
  min-width: 0;
  border-top: 1px solid #e7ece7;
}
.market-items-head,
.market-item-line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 27px minmax(45px, auto) minmax(45px, auto);
  align-items: center;
  gap: 4px;
  min-height: 29px;
  border-bottom: 1px solid #edf0ed;
  color: #677269;
  font-size: 7px;
}
.market-items-head {
  min-height: 25px;
  color: #88938b;
  font-size: 6px;
  font-weight: 700;
}
.market-items-head span:not(:first-child),
.market-item-line > span:not(:first-child),
.market-item-line > strong {
  text-align: right;
  white-space: nowrap;
}
.market-item-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.market-item-line > strong {
  color: #445148;
  font-size: 7px;
}
.market-item-line.missing {
  background: #fff1ef;
  color: #ad5147;
}
.market-item-line.missing strong {
  color: #bf493d;
  font-size: 6px;
}
.market-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 5px;
  margin-top: 10px;
  color: #455349;
  font-size: 8px;
  font-weight: 600;
}
.market-card-footer strong {
  color: #19864e;
  font-size: 13px;
  white-space: nowrap;
}
.totals-empty {
  display: flex;
  min-height: 95px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px dashed #dbe5dc;
  border-radius: 6px;
  color: #7c8980;
}
.totals-empty > span {
  color: #388458;
  font-size: 18px;
}
.totals-empty p {
  font-size: 10px;
}
.totals-error {
  padding: 9px 10px;
  border-left: 2px solid #b85d48;
  background: #fbefeb;
  color: #8c4838;
  font-size: 9px;
}
.calculate-list-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 38px;
  margin-top: 11px;
  border: 0;
  border-radius: 4px;
  background: #168b53;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
}
.calculate-list-button:disabled {
  background: #c8d4cb;
  cursor: not-allowed;
}
.shopping-totals.compact .totals-heading {
  margin-bottom: 8px;
}
.shopping-totals.compact .totals-heading h2 {
  font-size: 11px;
}
.shopping-totals.compact .totals-empty {
  min-height: 50px;
  border: 0;
  color: #8b968e;
}
.shopping-totals.compact .totals-empty > span {
  display: none;
}
.shopping-totals.compact .totals-empty p {
  margin: 0;
  font-size: 8px;
  text-align: center;
}
.shopping-totals.compact .market-grid {
  grid-template-columns: 1fr;
  gap: 6px;
}
.shopping-totals.compact .market-card {
  padding: 8px;
  border-radius: 4px;
}
.shopping-totals.compact .market-card-header {
  gap: 6px;
}
.shopping-totals.compact .market-logo {
  width: 25px;
  height: 25px;
  font-size: 10px;
}
.shopping-totals.compact .market-ident strong {
  font-size: 9px;
}
.shopping-totals.compact .market-ident small {
  font-size: 7px;
}
.shopping-totals.compact .market-status {
  padding: 3px 5px;
  font-size: 6px;
}
.shopping-totals.compact .market-card-total {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  margin: 7px 0 2px;
}
.shopping-totals.compact .market-card-total span {
  font-size: 8px;
}
.shopping-totals.compact .market-card-total strong {
  font-size: 12px;
}
.shopping-totals.compact .market-items-table,
.shopping-totals.compact .market-card-footer {
  display: none;
}
.shopping-totals.compact .calculate-list-button {
  min-height: 33px;
  margin-top: 9px;
  font-size: 8px;
}
@media (max-width: 1100px) {
  .market-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 700px) {
  .totals-heading {
    align-items: start;
    flex-direction: column;
  }
  .market-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 440px) {
  .market-grid {
    grid-template-columns: 1fr;
  }
  .totals-sort {
    width: 100%;
    justify-content: space-between;
  }
}
.market-best-label {
  margin: 0 0 10px;
  color: #187543;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
}

.market-total-difference {
  margin: 0 0 10px;
  color: #94651a;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.5;
}

/* Visual refinement: shared design language. */

.shopping-totals { min-width: 0; }
.totals-heading { align-items: center; margin-bottom: 18px; }
.totals-kicker { color: #5b8877; font-size: 10px; }
.totals-heading h2 { color: #1c3553; font-size: 22px; }
.totals-description { color: #73869c; font-size: 12px; line-height: 1.5; }
.totals-sort { color: #647a93; font-size: 11px; }
.totals-sort select { height: 38px; padding: 0 12px; border-color: #dce5ee; border-radius: 8px; color: #263f5d; font-size: 11px; }
.market-grid { gap: 14px; }
.market-card {
  padding: 16px 15px 14px;
  border-color: #e1e8f0;
  border-radius: 12px;
  box-shadow: 0 3px 12px rgb(24 48 77 / 4%);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}
.market-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgb(24 48 77 / 8%); }
.market-card.cheapest {
  border-color: #21a477;
  background: #f0fbf5;
  box-shadow: 0 0 0 1px #21a477, 0 5px 16px rgb(8 124 89 / 8%);
}
.market-card-header { gap: 10px; }
.market-logo { width: 40px; height: 40px; font-size: 14px; }
.market-ident { gap: 5px; }
.market-ident strong { color: #203752; font-size: 12px; }
.market-ident small { color: #74869a; font-size: 9px; }
.market-status { gap: 5px; padding: 5px 7px; font-size: 8px; }
.market-status i { font-size: 9px; }
.market-card-total { gap: 5px; margin: 17px 0 10px; }
.market-card-total span { color: #627991; font-size: 11px; }
.market-card-total strong { color: #087c59; font-size: 25px; line-height: 1.1; letter-spacing: -0.7px; }
.market-card.incomplete .market-card-total strong { color: #9b7025; }
.market-items-table { border-top-color: #e3eaf2; }
.market-items-head, .market-item-line { min-height: 33px; border-bottom-color: #edf1f5; color: #61758c; font-size: 9px; }
.market-items-head { min-height: 31px; color: #7e90a3; font-size: 8px; }
.market-item-line > strong { color: #334b66; font-size: 9px; }
.market-item-line.missing strong { font-size: 8px; }
.market-card-footer { margin-top: 12px; color: #415976; font-size: 10px; }
.market-card-footer strong { color: #087c59; font-size: 15px; }
.totals-empty { min-height: 130px; border-color: #d9e5ed; border-radius: 10px; background: #fff; }
.totals-empty > span { color: #087c59; }
.totals-empty p { color: #6e8298; font-size: 12px; }
.totals-error { border-radius: 7px; font-size: 11px; }
.calculate-list-button { min-height: 42px; border-radius: 8px; background: #087c59; font-size: 11px; }
.calculate-list-button:hover:not(:disabled) { background: #066848; }
.market-best-label { margin: 0 0 11px; color: #087452; font-size: 11px; line-height: 1.5; }
.market-total-difference { margin: 0 0 11px; padding: 10px; border-radius: 8px; background: #fff7e9; color: #996016; font-size: 10px; line-height: 1.5; }
.shopping-totals.compact .market-grid { gap: 8px; }
.shopping-totals.compact .market-card { padding: 10px; border-radius: 8px; }
.shopping-totals.compact .market-card-header { gap: 7px; }
.shopping-totals.compact .market-logo { width: 30px; height: 30px; font-size: 11px; }
.shopping-totals.compact .market-ident strong { font-size: 10px; }
.shopping-totals.compact .market-ident small { font-size: 8px; }
.shopping-totals.compact .market-status { padding: 3px 5px; font-size: 7px; }
.shopping-totals.compact .market-card-total { margin: 9px 0 3px; }
.shopping-totals.compact .market-card-total span { font-size: 9px; }
.shopping-totals.compact .market-card-total strong { font-size: 14px; }
.shopping-totals.compact .calculate-list-button { min-height: 36px; border-radius: 7px; font-size: 9px; }
@media (max-width: 1100px) {
  .market-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 700px) {
  .totals-heading { align-items: flex-start; }
  .totals-heading h2 { font-size: 19px; }
  .market-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .market-card { padding: 12px; }
  .market-card-header { flex-wrap: wrap; }
}
@media (max-width: 440px) {
  .market-grid { grid-template-columns: 1fr; }
  .market-card-header { flex-wrap: nowrap; }
  .market-card-total strong { font-size: 23px; }
}


/* Dedicated comparison page: visual hierarchy follows the supplied reference. */
.comparison-mode {
  min-width: 0;
}
.comparison-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin: 0 0 18px;
  color: #647a93;
  font-size: 11px;
}
.comparison-controls > span {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.sort-symbol {
  color: #54708e;
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
}
.comparison-sort-select select {
  min-width: 190px;
  height: 38px;
  padding: 0 12px;
  border: 1px solid #dce5ee;
  border-radius: 9px;
  background: #fff;
  color: #203752;
  font-size: 11px;
}
.comparison-market-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}
.comparison-market-card {
  position: relative;
  min-height: 285px;
  padding: 18px 18px 16px;
  border: 1px solid #e2eaf1;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 3px 13px rgb(24 48 77 / 5%);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}
.comparison-market-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 22px rgb(24 48 77 / 9%);
}
.comparison-market-card.cheapest {
  border-color: #18a477;
  background: linear-gradient(145deg, #fbfffc 0%, #f0fbf6 100%);
  box-shadow: 0 0 0 1px #18a477, 0 5px 18px rgb(8 124 89 / 8%);
}
.comparison-market-card.selected:not(.cheapest) {
  border-color: #8aa3bf;
  box-shadow: 0 0 0 1px #b4c5d6;
}
.comparison-card-heading {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 11px;
}
.comparison-market-logo {
  display: grid;
  width: 68px;
  height: 48px;
  flex: 0 0 auto;
  place-items: center;
  overflow: hidden;
  padding: 4px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #fff;
}
.comparison-market-logo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.comparison-market-logo > span {
  color: #087c59;
  font-size: 21px;
  font-weight: 800;
}
.comparison-market-ident {
  min-width: 0;
  gap: 6px;
}
.comparison-market-ident strong {
  color: #203752;
  font-size: 14px;
  line-height: 1.25;
}
.comparison-market-ident small {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #536d88;
  font-size: 10px;
  line-height: 1.4;
}
.coverage-indicator {
  display: inline-grid;
  width: 15px;
  height: 15px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: #e5f6ec;
  color: #0b9665;
  font-size: 10px;
  font-weight: 900;
}
.coverage-indicator.incompleto {
  background: #fff2d9;
  color: #d18a00;
}
.comparison-winner-pill {
  position: absolute;
  top: 12px;
  right: 13px;
  max-width: 90px;
  padding: 5px 9px;
  border-radius: 999px;
  background: #087c59;
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  line-height: 1;
  white-space: nowrap;
}
.comparison-total {
  gap: 7px;
  margin: 22px 0 14px;
}
.comparison-total span {
  color: #5e7590;
  font-size: 12px;
}
.comparison-total strong {
  color: #1e3046;
  font-size: clamp(23px, 2vw, 29px);
  font-weight: 800;
  letter-spacing: -0.7px;
  line-height: 1.1;
}
.comparison-market-card.cheapest .comparison-total strong {
  color: #087c59;
}
.comparison-market-card.incomplete .comparison-total strong {
  color: #9b7025;
}
.comparison-best-label {
  display: flex;
  min-height: 50px;
  align-items: center;
  gap: 10px;
  margin: 0 0 14px;
  padding: 11px 13px;
  border-radius: 9px;
  background: #e5f6ef;
  color: #087452;
  font-size: 11px;
  line-height: 1.4;
}
.comparison-best-label span {
  font-size: 17px;
}
.comparison-difference {
  display: flex;
  min-height: 50px;
  align-items: flex-start;
  gap: 9px;
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 9px;
  background: #fff6e8;
  color: #a96a00;
}
.comparison-difference > span:first-child {
  padding-top: 1px;
  font-size: 17px;
  font-weight: 800;
}
.comparison-difference > span:last-child {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.comparison-difference strong {
  font-size: 11px;
  line-height: 1.25;
}
.comparison-difference small {
  color: #79552c;
  font-size: 10px;
  line-height: 1.35;
}
.comparison-incomplete-note,
.comparison-equal-note {
  display: flex;
  min-height: 50px;
  align-items: center;
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 9px;
  background: #f4f7fa;
  color: #647991;
  font-size: 10px;
  line-height: 1.45;
}
.comparison-details-button {
  display: flex;
  width: 100%;
  min-height: 39px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: auto;
  padding: 0 12px;
  border: 1px solid #7990aa;
  border-radius: 8px;
  background: #fff;
  color: #173250;
  font-size: 11px;
  font-weight: 750;
  transition: background 160ms ease, border-color 160ms ease, color 160ms ease;
}
.comparison-details-button span {
  font-size: 15px;
  line-height: 1;
}
.comparison-details-button:hover,
.comparison-details-button.active:not(.primary) {
  border-color: #0b7b5b;
  background: #f4fbf7;
}
.comparison-details-button.primary {
  border-color: #087c59;
  background: #087c59;
  color: #fff;
}
.comparison-details-button.primary:hover {
  background: #06694b;
}
.comparison-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 2.15fr) minmax(260px, 0.82fr);
  align-items: stretch;
  gap: 17px;
  margin-top: 19px;
}
.comparison-breakdown {
  min-width: 0;
  overflow: hidden;
  border: 1px solid #e4ebf2;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 3px 13px rgb(24 48 77 / 4%);
}
.comparison-breakdown-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 17px 20px;
  border-bottom: 1px solid #e8eef4;
}
.comparison-detail-market {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}
.comparison-detail-logo {
  display: grid;
  width: 68px;
  height: 45px;
  flex: 0 0 auto;
  place-items: center;
  overflow: hidden;
  padding: 3px;
  border-radius: 8px;
  background: #fff;
}
.comparison-detail-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.comparison-detail-logo span {
  color: #087c59;
  font-size: 24px;
  font-weight: 800;
}
.comparison-detail-market h3 {
  margin: 0;
  color: #173250;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -0.3px;
}
.comparison-detail-market p {
  margin: 5px 0 0;
  color: #657d97;
  font-size: 10px;
}
.comparison-detail-cheapest {
  padding: 5px 9px;
  border-radius: 999px;
  background: #e4f6ee;
  color: #0a865c;
  font-size: 9px;
  font-weight: 800;
  white-space: nowrap;
}
.comparison-detail-total {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 0 0 auto;
  text-align: left;
}
.comparison-detail-total span {
  color: #5e7590;
  font-size: 11px;
}
.comparison-detail-total strong {
  color: #1b2e45;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.4px;
  line-height: 1.15;
}
.comparison-table-scroll {
  width: 100%;
  overflow-x: auto;
  padding: 0 18px 15px;
}
.comparison-products-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  color: #3f5876;
  font-size: 11px;
  text-align: left;
}
.comparison-products-table th {
  padding: 11px 10px;
  border-bottom: 1px solid #e5edf4;
  background: #f5f8fb;
  color: #667f9d;
  font-size: 10px;
  font-weight: 750;
  white-space: nowrap;
}
.comparison-products-table th:first-child {
  border-radius: 7px 0 0 0;
}
.comparison-products-table th:last-child {
  border-radius: 0 7px 0 0;
}
.comparison-products-table td {
  padding: 11px 10px;
  border-bottom: 1px solid #eef2f6;
  vertical-align: middle;
  white-space: nowrap;
}
.comparison-products-table tbody tr:last-child td {
  border-bottom: 0;
}
.comparison-products-table td:not(:first-child),
.comparison-products-table th:not(:first-child) {
  text-align: right;
}
.comparison-product-cell {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}
.comparison-product-cell img {
  display: block;
  width: 27px;
  height: 34px;
  flex: 0 0 auto;
  object-fit: contain;
}
.comparison-products-table .comparison-product-name {
  display: block;
  min-width: 150px;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.comparison-products-table .comparison-subtotal {
  color: #2e4c69;
  font-weight: 750;
}
.comparison-product-missing td {
  background: #fff7f5;
  color: #ad5147;
}
.comparison-products-table .comparison-no-products {
  padding: 24px 12px;
  color: #7b8da2;
  text-align: center !important;
}
.comparison-insights {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 12px;
}
.comparison-insight-card {
  display: flex;
  gap: 12px;
  padding: 16px 15px;
  border: 1px solid #e5edf3;
  border-radius: 12px;
  background: #fff;
}
.savings-tip {
  border-color: #e0f0e8;
  background: linear-gradient(135deg, #f0faf5 0%, #eaf8f1 100%);
}
.comparison-insight-icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: #d8f0e5;
  color: #087c59;
  font-size: 20px;
}
.comparison-insight-card h3 {
  margin: 0 0 7px;
  color: #087452;
  font-size: 12px;
  font-weight: 800;
}
.comparison-insight-card p {
  margin: 0;
  color: #29425d;
  font-size: 11px;
  line-height: 1.55;
}
.comparison-insight-card p strong {
  color: #173250;
  font-weight: 800;
}
.list-summary {
  display: block;
  background: #f6f9fc;
}
.list-summary-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #1c3b5d;
}
.list-summary-title > span {
  font-size: 18px;
}
.list-summary-title h3 {
  margin: 0;
  color: #1c3b5d;
  font-size: 12px;
}
.list-summary-line {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 5px 0;
  color: #607895;
  font-size: 10px;
  line-height: 1.4;
}
.list-summary-line strong {
  color: #304b6a;
  font-size: 10px;
  font-weight: 700;
  text-align: right;
}
.list-summary-line.summary-total {
  margin-top: 5px;
  padding-top: 10px;
  border-top: 1px solid #e0e9f1;
}
.list-summary-line.summary-total strong {
  color: #087c59;
  font-size: 14px;
  white-space: nowrap;
}
.comparison-edit-list {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding: 8px 0 0;
  border: 0;
  border-top: 1px solid #e0e9f1;
  background: transparent;
  color: #1f456e;
  font-size: 10px;
  font-weight: 750;
  text-align: left;
}
.comparison-edit-list:hover {
  color: #087c59;
}
.comparison-recalculate {
  max-width: 280px;
  margin: 17px 0 0 auto;
}
.comparison-empty {
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 14px;
  padding: 24px;
  border: 1px solid #e1eaf1;
  border-radius: 12px;
  background: #fff;
}
.comparison-empty-icon {
  display: grid;
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: #e4f6ee;
  color: #087c59;
  font-size: 22px;
}
.comparison-empty-copy {
  min-width: 0;
  flex: 1;
}
.comparison-empty-copy strong {
  color: #173250;
  font-size: 14px;
}
.comparison-empty-copy p {
  margin: 5px 0 0;
  color: #687f98;
  font-size: 11px;
  line-height: 1.5;
}
.comparison-empty-action {
  min-height: 37px;
  padding: 0 13px;
  border: 0;
  border-radius: 8px;
  background: #087c59;
  color: #fff;
  font-size: 11px;
  font-weight: 750;
}
.comparison-empty-action:disabled {
  opacity: .65;
  cursor: wait;
}
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1120px) {
  .comparison-market-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .comparison-detail-grid {
    grid-template-columns: minmax(0, 1.6fr) minmax(245px, .9fr);
  }
}
@media (max-width: 850px) {
  .comparison-detail-grid {
    grid-template-columns: 1fr;
  }
  .comparison-insights {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: stretch;
  }
}
@media (max-width: 620px) {
  .comparison-controls {
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }
  .comparison-sort-select {
    min-width: 0;
    flex: 1;
  }
  .comparison-sort-select select {
    width: 100%;
    min-width: 0;
  }
  .comparison-market-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .comparison-market-card {
    min-height: 0;
  }
  .comparison-total strong {
    font-size: 25px;
  }
  .comparison-breakdown-heading {
    align-items: flex-start;
    flex-direction: column;
    padding: 14px;
  }
  .comparison-detail-total {
    padding-left: 80px;
  }
  .comparison-table-scroll {
    padding: 0 10px 10px;
  }
  .comparison-products-table {
    min-width: 520px;
  }
  .comparison-insights {
    grid-template-columns: 1fr;
  }
  .comparison-recalculate {
    max-width: none;
  }
  .comparison-empty {
    padding: 18px;
  }
}
</style>

<style>
/* Exibe a marca do supermercado como logotipo, não como avatar colorido. */
.market-card-header .market-logo {
  width: 76px;
  height: 38px;
  padding: 4px 6px;
  border: 1px solid #e8edf2;
  border-radius: 8px;
  background: #fff;
  color: #18324d;
}
.market-card-header .market-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.comparison-market-logo {
  width: 66px !important;
  height: 44px !important;
  padding: 4px 6px;
  border: 1px solid #e8edf2;
  border-radius: 8px !important;
  background: #fff !important;
}
.comparison-market-logo img {
  object-fit: contain;
}
.comparison-detail-logo {
  width: 58px;
  height: 42px;
  padding: 4px 5px;
  border: 1px solid #e8edf2;
  border-radius: 8px;
  background: #fff;
}
.comparison-detail-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
