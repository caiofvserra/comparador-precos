<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useShoppingList } from '../composables/useShoppingList'
import { isDemoData } from '../services/api'

const router = useRouter()
const { basketProducts } = useShoppingList()
const listCountText = computed(() => {
  const count = basketProducts.value.length
  return `${count} ${count === 1 ? 'produto' : 'produtos'} na sua lista`
})

function browseProducts() {
  void router.push({ name: 'catalog', hash: '#product-search' })
}

function openList() {
  void router.push({ name: 'shopping-list' })
}

function openComparison() {
  void router.push({ name: basketProducts.value.length ? 'comparison' : 'shopping-list' })
}
</script>

<template>
  <div class="mvp-app landing-home">
    <main class="landing-main">
      <section class="landing-hero" aria-labelledby="landing-title">
        <div class="landing-hero-copy">
          <p class="landing-eyebrow"><span></span> COMPARADOR DE PREÇOS • RIBEIRÃO PRETO</p>
          <h1 id="landing-title">Sua compra mais inteligente <em>começa aqui.</em></h1>
          <p class="landing-lede">
            Pesquise produtos, monte sua lista e descubra onde sua compra pode sair mais em conta —
            tudo em um só lugar.
          </p>
          <div class="landing-actions">
            <button class="landing-button primary" type="button" @click="browseProducts">
              Buscar produtos <span aria-hidden="true">→</span>
            </button>
            <button class="landing-button secondary" type="button" @click="openList">
              <span aria-hidden="true">＋</span> Montar minha lista
            </button>
          </div>
          <p v-if="isDemoData" class="landing-demo-note">
            <span aria-hidden="true">ⓘ</span> Os preços desta versão são demonstrativos, não ofertas
            em tempo real.
          </p>
        </div>
        <div class="landing-hero-visual">
          <img
            src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1100&q=85"
            alt="Hortifrúti e alimentos frescos em um supermercado"
          />
          <div class="landing-floating-card">
            <span class="landing-floating-icon" aria-hidden="true">✓</span>
            <div>
              <strong>Planeje antes de comprar</strong>
              <small>Compare a lista completa entre supermercados</small>
            </div>
          </div>
        </div>
        <div class="landing-hero-decoration" aria-hidden="true"></div>
      </section>

      <section class="landing-benefits" aria-label="O que você pode fazer">
        <button class="landing-feature" type="button" @click="browseProducts">
          <span class="landing-feature-icon search-icon" aria-hidden="true">⌕</span>
          <span class="landing-feature-copy">
            <strong>Encontre seus produtos</strong>
            <small>Busque por nome, marca ou categoria no catálogo.</small>
          </span>
          <span class="landing-feature-arrow" aria-hidden="true">↗</span>
        </button>
        <button class="landing-feature" type="button" @click="openList">
          <span class="landing-feature-icon list-icon" aria-hidden="true">☷</span>
          <span class="landing-feature-copy">
            <strong>Organize sua lista</strong>
            <small>Adicione itens e ajuste as quantidades que precisa.</small>
          </span>
          <span class="landing-feature-arrow" aria-hidden="true">↗</span>
        </button>
        <button class="landing-feature" type="button" @click="openComparison">
          <span class="landing-feature-icon chart-icon" aria-hidden="true">▥</span>
          <span class="landing-feature-copy">
            <strong>Compare supermercados</strong>
            <small>Confira os totais e identifique a melhor opção completa.</small>
          </span>
          <span class="landing-feature-arrow" aria-hidden="true">↗</span>
        </button>
      </section>

      <section class="landing-how" aria-labelledby="landing-how-title">
        <div class="landing-section-heading">
          <p class="landing-eyebrow">UM FLUXO SIMPLES</p>
          <h2 id="landing-how-title">Da pesquisa à decisão, sem complicação.</h2>
          <p>Três passos para deixar sua compra mais organizada.</p>
        </div>
        <div class="landing-steps">
          <article class="landing-step">
            <span class="landing-step-number">01</span>
            <div>
              <h3>Pesquise</h3>
              <p>Encontre os produtos que fazem parte da sua compra.</p>
            </div>
          </article>
          <article class="landing-step">
            <span class="landing-step-number">02</span>
            <div>
              <h3>Monte sua lista</h3>
              <p>Defina os itens e as quantidades antes de comparar.</p>
            </div>
          </article>
          <article class="landing-step">
            <span class="landing-step-number">03</span>
            <div>
              <h3>Compare</h3>
              <p>Veja os resultados e os itens disponíveis por mercado.</p>
            </div>
          </article>
        </div>
      </section>

      <section class="landing-market-strip" aria-label="Supermercados presentes no projeto">
        <div class="landing-market-copy">
          <strong>Compare em um só lugar</strong>
          <span>Supermercados contemplados no projeto</span>
        </div>
        <div class="landing-market-logos">
          <img src="/logos/atacadao.svg" alt="Atacadão" />
          <img src="/logos/savegnago.svg" alt="Savegnago" />
          <img src="/logos/carrefour.svg" alt="Carrefour" />
        </div>
      </section>

      <section class="landing-last-cta">
        <div>
          <p class="landing-eyebrow">VAMOS COMEÇAR?</p>
          <h2>{{ listCountText }}</h2>
          <p>Continue de onde estiver: procure um produto ou revise sua lista.</p>
        </div>
        <div class="landing-last-actions">
          <button class="landing-button secondary" type="button" @click="openList">
            Abrir minha lista
          </button>
          <button class="landing-button primary" type="button" @click="browseProducts">
            Buscar produtos <span aria-hidden="true">→</span>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.landing-main {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-top: 22px;
  padding-bottom: 34px;
}
.landing-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.85fr);
  align-items: center;
  gap: 28px;
  min-height: 338px;
  padding: 36px;
  overflow: hidden;
  border: 1px solid #dfeee6;
  border-radius: 20px;
  background: linear-gradient(118deg, #f8fcfa 0%, #eaf7f0 60%, #e1f2e8 100%);
  box-shadow: var(--mvp-shadow);
  isolation: isolate;
}
.landing-hero-copy {
  position: relative;
  z-index: 2;
  max-width: 610px;
}
.landing-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 13px;
  color: #36785f;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.15px;
  line-height: 1.5;
}
.landing-eyebrow > span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #12a477;
  box-shadow: 0 0 0 4px #d9f1e4;
}
.landing-hero h1 {
  max-width: 570px;
  margin: 0;
  color: #142b49;
  font-size: clamp(32px, 3.4vw, 48px);
  font-weight: 800;
  letter-spacing: -1.8px;
  line-height: 1.08;
}
.landing-hero h1 em {
  color: #087c59;
  font-style: normal;
}
.landing-lede {
  max-width: 520px;
  margin: 17px 0 0;
  color: #5d7184;
  font-size: 14px;
  line-height: 1.75;
}
.landing-actions,
.landing-last-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 24px;
}
.landing-button {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 17px;
  border: 1px solid transparent;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 750;
  transition:
    transform 160ms ease,
    background 160ms ease,
    box-shadow 160ms ease;
}
.landing-button:hover {
  transform: translateY(-1px);
}
.landing-button.primary {
  background: #087c59;
  color: #fff;
  box-shadow: 0 5px 14px rgb(8 124 89 / 18%);
}
.landing-button.primary:hover {
  background: #066c4d;
  box-shadow: 0 7px 18px rgb(8 124 89 / 24%);
}
.landing-button.secondary {
  border-color: #d6e4dd;
  background: rgb(255 255 255 / 86%);
  color: #173653;
}
.landing-button.secondary:hover {
  border-color: #a8c9b8;
  background: #fff;
}
.landing-demo-note {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin: 16px 0 0;
  color: #7b897f;
  font-size: 10px;
  line-height: 1.5;
}
.landing-hero-visual {
  position: relative;
  z-index: 1;
  min-width: 0;
  padding: 5px 0 18px 4px;
}
.landing-hero-visual > img {
  display: block;
  width: 100%;
  height: 255px;
  object-fit: cover;
  object-position: center;
  border-radius: 16px;
  box-shadow: 0 15px 35px rgb(29 63 50 / 16%);
}
.landing-floating-card {
  position: absolute;
  right: -12px;
  bottom: 0;
  display: flex;
  max-width: 290px;
  align-items: center;
  gap: 11px;
  padding: 13px 15px;
  border: 1px solid #e0eee6;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 9px 24px rgb(22 52 40 / 13%);
}
.landing-floating-icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  place-items: center;
  border-radius: 50%;
  background: #e5f7ed;
  color: #087c59;
  font-size: 18px;
  font-weight: 800;
}
.landing-floating-card div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.landing-floating-card strong {
  color: #18324c;
  font-size: 11px;
}
.landing-floating-card small {
  color: #77899a;
  font-size: 9px;
  line-height: 1.4;
}
.landing-hero-decoration {
  position: absolute;
  z-index: -1;
  top: -135px;
  right: 34%;
  width: 270px;
  height: 270px;
  border: 1px solid rgb(8 124 89 / 7%);
  border-radius: 50%;
  box-shadow:
    0 0 0 30px rgb(8 124 89 / 3%),
    0 0 0 60px rgb(8 124 89 / 2%);
}
.landing-benefits {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.landing-feature {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
  padding: 17px;
  border: 1px solid var(--mvp-line);
  border-radius: 13px;
  background: #fff;
  color: inherit;
  text-align: left;
  box-shadow: var(--mvp-shadow);
  transition:
    transform 150ms ease,
    border-color 150ms ease,
    box-shadow 150ms ease;
}
.landing-feature:hover {
  transform: translateY(-2px);
  border-color: #c4dfd0;
  box-shadow: 0 8px 20px rgb(24 48 77 / 8%);
}
.landing-feature-icon {
  display: grid;
  width: 43px;
  height: 43px;
  flex: 0 0 43px;
  place-items: center;
  border-radius: 12px;
  background: #e9f7f0;
  color: #087c59;
  font-size: 27px;
  font-weight: 700;
}
.landing-feature-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 5px;
}
.landing-feature-copy strong {
  color: #172f4d;
  font-size: 12px;
}
.landing-feature-copy small {
  color: #718399;
  font-size: 10px;
  line-height: 1.55;
}
.landing-feature-arrow {
  align-self: flex-start;
  color: #77a18d;
  font-size: 15px;
}
.landing-how {
  padding: 27px 28px 26px;
  border: 1px solid var(--mvp-line);
  border-radius: 15px;
  background: linear-gradient(135deg, #fff 0%, #f9fbfd 100%);
}
.landing-section-heading {
  text-align: center;
}
.landing-section-heading .landing-eyebrow {
  justify-content: center;
  margin-bottom: 8px;
}
.landing-section-heading h2 {
  margin: 0;
  color: #142b49;
  font-size: clamp(21px, 2.2vw, 28px);
  font-weight: 800;
  letter-spacing: -0.75px;
}
.landing-section-heading > p:last-child {
  margin: 8px 0 0;
  color: #718399;
  font-size: 12px;
}
.landing-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 13px;
  margin-top: 24px;
}
.landing-step {
  display: flex;
  align-items: flex-start;
  gap: 13px;
  padding: 16px;
  border: 1px solid #e6edf2;
  border-radius: 11px;
  background: #f8fafc;
}
.landing-step-number {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  place-items: center;
  border-radius: 10px;
  background: #dff3e8;
  color: #087c59;
  font-size: 11px;
  font-weight: 800;
}
.landing-step h3 {
  margin: 2px 0 0;
  color: #18324d;
  font-size: 12px;
}
.landing-step p {
  margin: 6px 0 0;
  color: #78889a;
  font-size: 10px;
  line-height: 1.55;
}
.landing-market-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 20px 24px;
  border: 1px solid var(--mvp-line);
  border-radius: 13px;
  background: #fff;
}
.landing-market-copy {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.landing-market-copy strong {
  color: #18324d;
  font-size: 12px;
}
.landing-market-copy span {
  color: #7c8da0;
  font-size: 10px;
}
.landing-market-logos {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: clamp(20px, 4vw, 48px);
  flex-wrap: wrap;
}
.landing-market-logos img {
  display: block;
  width: auto;
  max-width: 120px;
  height: 32px;
  object-fit: contain;
}
.landing-last-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 22px 25px;
  border: 1px solid #dcece3;
  border-radius: 14px;
  background: #eff8f3;
}
.landing-last-cta .landing-eyebrow {
  margin-bottom: 6px;
}
.landing-last-cta h2 {
  margin: 0;
  color: #173250;
  font-size: 19px;
  letter-spacing: -0.4px;
}
.landing-last-cta p:last-child {
  margin: 6px 0 0;
  color: #6e8278;
  font-size: 11px;
}
.landing-last-actions {
  flex: 0 0 auto;
  justify-content: flex-end;
  margin: 0;
}
@media (max-width: 1080px) {
  .landing-hero {
    gap: 20px;
    padding: 28px;
  }
  .landing-hero h1 {
    font-size: clamp(30px, 3.5vw, 40px);
  }
  .landing-hero-visual > img {
    height: 225px;
  }
  .landing-benefits {
    gap: 10px;
  }
  .landing-feature {
    gap: 9px;
    padding: 13px;
  }
  .landing-feature-icon {
    width: 38px;
    height: 38px;
    flex-basis: 38px;
  }
}
@media (max-width: 820px) {
  .landing-main {
    gap: 15px;
    padding-top: 15px;
  }
  .landing-hero {
    grid-template-columns: 1fr;
    gap: 18px;
    padding: 23px;
  }
  .landing-hero-copy {
    max-width: 680px;
  }
  .landing-hero h1 {
    max-width: 600px;
    font-size: clamp(29px, 5vw, 39px);
  }
  .landing-hero-visual {
    max-width: 570px;
    padding-right: 10px;
  }
  .landing-hero-visual > img {
    height: 220px;
  }
  .landing-floating-card {
    right: 0;
  }
  .landing-benefits,
  .landing-steps {
    grid-template-columns: 1fr;
  }
  .landing-market-strip,
  .landing-last-cta {
    align-items: flex-start;
    flex-direction: column;
  }
  .landing-market-logos {
    justify-content: flex-start;
  }
  .landing-last-actions {
    justify-content: flex-start;
  }
}
@media (max-width: 480px) {
  .landing-hero {
    padding: 18px;
    border-radius: 14px;
  }
  .landing-hero h1 {
    font-size: 30px;
    letter-spacing: -1px;
  }
  .landing-lede {
    font-size: 12px;
  }
  .landing-actions,
  .landing-last-actions {
    align-items: stretch;
    flex-direction: column;
  }
  .landing-button {
    width: 100%;
  }
  .landing-hero-visual > img {
    height: 175px;
  }
  .landing-floating-card {
    right: 0;
    max-width: calc(100% - 6px);
    padding: 10px;
  }
  .landing-how {
    padding: 21px 14px;
  }
  .landing-market-strip,
  .landing-last-cta {
    padding: 17px;
  }
  .landing-market-logos {
    gap: 20px;
  }
  .landing-market-logos img {
    max-width: 96px;
    height: 27px;
  }
}
</style>
