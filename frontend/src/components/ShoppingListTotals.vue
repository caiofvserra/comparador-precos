<script setup lang="ts">
import { computed, ref } from 'vue'
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
  }>(),
  { loading: false, error: '', compact: false, showHeading: true },
)

const emit = defineEmits<{ calculate: [] }>()
const orderBy = ref('total')
const orderedMarkets = computed(() => {
  const results = [...(props.simulation?.supermercados ?? [])]
  return results.sort((first, second) => {
    if (orderBy.value === 'market')
      return first.supermercado.nome.localeCompare(second.supermercado.nome, 'pt-BR')
    if (first.status !== second.status) return first.status === 'completo' ? -1 : 1
    return Number(first.total) - Number(second.total)
  })
})

function formatPrice(value: string) {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function productName(productId: number) {
  return props.products.find((product) => product.id === productId)?.nome || `Produto ${productId}`
}

function coverage(result: SupermarketResult) {
  const total = props.simulation?.total_itens ?? 0
  return `${result.itens_encontrados} de ${total} ${total === 1 ? 'item encontrado' : 'itens encontrados'}`
}
</script>

<template>
  <section class="shopping-totals" :class="{ compact }" aria-labelledby="shopping-totals-title">
    <header v-if="showHeading" class="totals-heading">
      <div>
        <p v-if="!compact" class="totals-kicker">COMPARAÇÃO DA LISTA</p>
        <h2 id="shopping-totals-title">Totais por supermercado</h2>
        <p v-if="!compact" class="totals-description">
          Totais oficiais calculados com o preço coletado mais recente de cada item.
        </p>
      </div>
      <label v-if="simulation && !compact" class="totals-sort"
        ><span>Ordenar por</span
        ><select v-model="orderBy">
          <option value="total">Menor total completo</option>
          <option value="market">Nome do mercado</option>
        </select></label
      >
    </header>

    <p v-if="error" class="totals-error" role="alert">{{ error }}</p>
    <div v-if="!simulation" class="totals-empty">
      <span aria-hidden="true">▥</span>
      <p>
        {{
          itemCount
            ? 'Calcule sua lista para comparar os mercados.'
            : 'Adicione produtos antes de calcular os totais.'
        }}
      </p>
    </div>
    <div v-else class="market-grid">
      <article
        v-for="(result, index) in orderedMarkets"
        :key="result.supermercado.id"
        class="market-card"
        :class="[
          { incomplete: result.status === 'incompleto' },
          { cheapest: result.status === 'completo' && index === 0 },
        ]"
      >
        <header class="market-card-header">
          <span class="market-logo" :class="`market-logo-${result.supermercado.id}`">{{
            result.supermercado.nome.slice(0, 1)
          }}</span>
          <div class="market-ident">
            <strong>{{ result.supermercado.nome }}</strong
            ><small>{{ coverage(result) }}</small>
          </div>
          <span class="market-status" :class="result.status"
            ><i aria-hidden="true">{{ result.status === 'completo' ? '✓' : '!' }}</i
            >{{ result.status === 'completo' ? 'Lista completa' : 'Lista incompleta' }}</span
          >
        </header>
        <div class="market-card-total">
          <span>{{
            result.status === 'completo'
              ? 'Valor total estimado'
              : `Total estimado (${result.itens_encontrados} itens)`
          }}</span
          ><strong>{{ formatPrice(result.total) }}</strong>
        </div>
        <div class="market-items-table">
          <div class="market-items-head">
            <span>Produto</span><span>Qtd.</span><span>Valor unitário</span><span>Subtotal</span>
          </div>
          <div v-for="item in result.itens" :key="item.produto_id" class="market-item-line">
            <span class="market-item-name">{{ productName(item.produto_id) }}</span>
            <span>{{ item.quantidade }}</span>
            <span>{{ formatPrice(item.valor_unitario) }}</span>
            <strong>{{ formatPrice(item.subtotal) }}</strong>
          </div>
          <div
            v-for="productId in result.itens_ausentes"
            :key="productId"
            class="market-item-line missing"
          >
            <span class="market-item-name">{{ productName(productId) }}</span
            ><span>—</span><span>—</span><strong>Não encontrado</strong>
          </div>
        </div>
        <footer class="market-card-footer">
          <span>{{ result.status === 'completo' ? 'Total estimado' : 'Total parcial' }}</span
          ><strong>{{ formatPrice(result.total) }}</strong>
        </footer>
      </article>
    </div>
    <button
      class="calculate-list-button"
      type="button"
      :disabled="itemCount === 0 || loading"
      @click="emit('calculate')"
    >
      <span aria-hidden="true">{{ loading ? '◌' : '▥' }}</span
      >{{ loading ? 'Calculando totais…' : 'Calcular totais por supermercado' }}
    </button>
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
.market-card.cheapest {
  border-color: #44aa73;
  box-shadow: 0 0 0 1px #44aa73;
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
</style>
