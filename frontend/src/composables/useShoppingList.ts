import { computed, ref } from 'vue'
import { getProducts, simulateList, type Product, type Simulation } from '../services/api'

export type BasketItem = { produto_id: number; quantidade: number }
export type ShoppingListEntry = BasketItem & { product: Product | undefined; imageUrl: string }

const productPhotos: Record<number, string> = {
  101: 'photo-1586201375761-83865001e31c',
  205: 'photo-1474979266404-7eaacbcd87c5',
  309: 'photo-1559056199-641a0ac8b55e',
  412: 'photo-1563636619-e9143da7973b',
  518: 'photo-1509440159596-0249088772ff',
  623: 'photo-1571771894821-ce9b6c11b08e',
}
const photosByProductName = [
  { terms: ['arroz'], photo: 'photo-1586201375761-83865001e31c' },
  { terms: ['azeite', 'oleo'], photo: 'photo-1474979266404-7eaacbcd87c5' },
  { terms: ['cafe'], photo: 'photo-1559056199-641a0ac8b55e' },
  { terms: ['leite'], photo: 'photo-1563636619-e9143da7973b' },
  { terms: ['pao'], photo: 'photo-1509440159596-0249088772ff' },
  { terms: ['banana'], photo: 'photo-1571771894821-ce9b6c11b08e' },
]

const basket = ref<BasketItem[]>([])
const knownProducts = ref<Product[]>([])
const simulation = ref<Simulation | null>(null)
const simulating = ref(false)
const simulationError = ref('')
const lastViewedProductId = ref<number | null>(null)
const basketCount = computed(() => basket.value.reduce((total, item) => total + item.quantidade, 0))
const basketProducts = computed(() =>
  basket.value.map((item): ShoppingListEntry => {
    const product = knownProducts.value.find((entry) => entry.id === item.produto_id)
    return { ...item, product, imageUrl: product ? productImageUrl(product) : '' }
  }),
)
let catalogPromise: Promise<Product[]> | undefined
let simulationSequence = 0

export function productTitle(product: Product | null | undefined) {
  return product?.nome?.replace(/\s+/g, ' ').trim() || `Produto ${product?.id ?? ''}`.trim()
}

export function productImageUrl(product: Product) {
  const productWithImage = product as Product & {
    imagem_url?: string | null
    image_url?: string | null
  }
  const providedUrl = productWithImage.imagem_url || productWithImage.image_url
  if (providedUrl) return providedUrl
  const normalizedName = productTitle(product)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR')
  const photo =
    photosByProductName.find(({ terms }) => terms.some((term) => normalizedName.includes(term)))
      ?.photo ?? productPhotos[product.id]
  return photo ? `https://images.unsplash.com/${photo}?auto=format&fit=crop&w=480&q=80` : ''
}

export function rememberProducts(products: Product[]) {
  knownProducts.value = [
    ...new Map(
      [...knownProducts.value, ...products].map((product) => [product.id, product]),
    ).values(),
  ]
}

export async function loadCatalog() {
  if (knownProducts.value.length) return knownProducts.value
  if (!catalogPromise) {
    catalogPromise = getProducts()
      .then((products) => {
        rememberProducts(products)
        return products
      })
      .finally(() => {
        catalogPromise = undefined
      })
  }
  return catalogPromise
}

export async function searchCatalog(query: string) {
  const products = await getProducts(query)
  rememberProducts(products)
  return products
}

export function addToBasket(product: Product) {
  rememberProducts([product])
  const existingItem = basket.value.find((item) => item.produto_id === product.id)
  if (existingItem) {
    if (existingItem.quantidade < 1000) existingItem.quantidade += 1
  } else {
    basket.value.push({ produto_id: product.id, quantidade: 1 })
  }
  simulation.value = null
  simulationError.value = ''
}

export function changeBasketQuantity(productId: number, quantity: number) {
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) return
  const item = basket.value.find((entry) => entry.produto_id === productId)
  if (item) item.quantidade = quantity
  simulation.value = null
  simulationError.value = ''
}

export function removeFromBasket(productId: number) {
  basket.value = basket.value.filter((item) => item.produto_id !== productId)
  simulation.value = null
  simulationError.value = ''
}

export async function calculateBasket() {
  if (!basket.value.length) return
  const requestId = ++simulationSequence
  simulating.value = true
  simulationError.value = ''
  try {
    const result = await simulateList({
      itens: basket.value.map(({ produto_id, quantidade }) => ({ produto_id, quantidade })),
    })
    if (requestId === simulationSequence) simulation.value = result
  } catch (error) {
    if (requestId === simulationSequence) {
      simulationError.value = error instanceof Error ? error.message : 'Falha ao simular a lista.'
    }
  } finally {
    if (requestId === simulationSequence) simulating.value = false
  }
}

export function useShoppingList() {
  return {
    basket,
    basketCount,
    basketProducts,
    knownProducts,
    simulation,
    simulating,
    simulationError,
    lastViewedProductId,
    rememberProducts,
    addToBasket,
    changeBasketQuantity,
    removeFromBasket,
    calculateBasket,
    loadCatalog,
    searchCatalog,
  }
}
