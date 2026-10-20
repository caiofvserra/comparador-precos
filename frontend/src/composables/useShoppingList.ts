import { computed, ref } from 'vue'
import { getProducts, simulateList, type Product, type Simulation } from '../services/api'

export type BasketItem = { produto_id: number; quantidade: number }
export type ShoppingListEntry = BasketItem & { product: Product | undefined; imageUrl: string }

const productPhotos: Record<number, string> = {
  101: '/images/products/101.svg',
  205: '/images/products/205.svg',
  309: '/images/products/309.svg',
  412: '/images/products/412.svg',
  518: '/images/products/518.svg',
  623: '/images/products/623.svg',
  744: '/images/products/744.svg',
  855: '/images/products/855.svg',
  966: '/images/products/966.svg',
  1077: '/images/products/1077.svg',
}

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
    return {
      ...item,
      product,
      imageUrl: product ? productImageUrl(product) : '/images/products/generic.svg',
    }
  }),
)
let catalogPromise: Promise<Product[]> | undefined
let simulationSequence = 0

export function productTitle(product: Product | null | undefined) {
  return product?.nome?.replace(/\s+/g, ' ').trim() || `Produto ${product?.id ?? ''}`.trim()
}

function normalizeText(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('pt-BR')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function normalizedProductName(product: Product) {
  return normalizeText(productTitle(product))
}

function localCatalogImageUrl(product: Product): string | undefined {
  const name = normalizedProductName(product)
  const brand = normalizeText(product.marca ?? '')
  const description = `${name} ${brand}`

  // The local photographs are matched by product name/brand rather than ID,
  // since IDs may differ between demo data and the connected API.
  if (name.includes('leite') && name.includes('desnatado')) {
    return '/images/products/leite-desnatado-itambe.png'
  }
  if (name.includes('leite') && name.includes('integral')) {
    return '/images/products/leite-integral-piracanjuba.png'
  }
  if (name.includes('arroz') && (name.includes('integral') || brand.includes('camil'))) {
    return '/images/products/arroz-integral-camil.png'
  }
  if (name.includes('azeite') && (name.includes('virgem') || brand.includes('gallo'))) {
    return '/images/products/azeite-extra-virgem-gallo.png'
  }
  if (name.includes('cafe') && (name.includes('tradicional') || brand.includes('melitta'))) {
    return '/images/products/cafe-tradicional-melitta.png'
  }
  if (name.includes('pao') && name.includes('italiano')) {
    return '/images/products/pao-italiano.png'
  }
  if (name.includes('banana') && name.includes('nanica')) {
    return '/images/products/banana-nanica.png'
  }
  if (name.includes('detergente') && (brand.includes('ype') || name.includes('500 ml'))) {
    return '/images/products/detergente-ype-500ml.jpg'
  }
  if (name.includes('sabonete') && (name.includes('glicerinado') || brand.includes('dove'))) {
    return '/images/products/sabonete-glicerinado-dove.png'
  }
  if (
    (name.includes('refrigerante') && name.includes('cola')) ||
    description.includes('coca cola')
  ) {
    return '/images/products/refrigerante-cola-cocacola.png'
  }

  return undefined
}

export function productFallbackImageUrl(product: Product | null | undefined) {
  if (!product) return '/images/products/generic.svg'
  const mappedPhoto = productPhotos[product.id]
  if (mappedPhoto) return mappedPhoto

  const normalizedName = normalizedProductName(product)
  if (
    normalizedName.includes('arroz') ||
    normalizedName.includes('feijao') ||
    normalizedName.includes('acucar')
  )
    return '/images/products/101.svg'
  if (normalizedName.includes('azeite') || normalizedName.includes('oleo'))
    return '/images/products/205.svg'
  if (normalizedName.includes('cafe')) return '/images/products/309.svg'
  if (
    normalizedName.includes('leite') ||
    normalizedName.includes('iogurte') ||
    normalizedName.includes('queijo')
  )
    return '/images/products/412.svg'
  if (
    normalizedName.includes('pao') ||
    normalizedName.includes('bolo') ||
    normalizedName.includes('biscoito')
  )
    return '/images/products/518.svg'
  if (
    normalizedName.includes('banana') ||
    normalizedName.includes('fruta') ||
    normalizedName.includes('verdura')
  )
    return '/images/products/623.svg'
  if (
    normalizedName.includes('detergente') ||
    normalizedName.includes('limpeza') ||
    normalizedName.includes('sabao')
  )
    return '/images/products/744.svg'
  if (
    normalizedName.includes('sabonete') ||
    normalizedName.includes('shampoo') ||
    normalizedName.includes('higiene')
  )
    return '/images/products/855.svg'
  if (
    normalizedName.includes('refrigerante') ||
    normalizedName.includes('cola') ||
    normalizedName.includes('suco') ||
    normalizedName.includes('agua')
  )
    return '/images/products/966.svg'

  const categories = (product.categorias ?? []).map((category) =>
    category
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLocaleLowerCase('pt-BR'),
  )
  if (categories.some((category) => category.includes('limpeza'))) return '/images/products/744.svg'
  if (categories.some((category) => category.includes('higiene'))) return '/images/products/855.svg'
  if (
    categories.some((category) => category.includes('bebidas') || category.includes('laticinios'))
  )
    return '/images/products/412.svg'
  if (
    categories.some(
      (category) =>
        category.includes('alimentos') ||
        category.includes('mercearia') ||
        category.includes('padaria'),
    )
  )
    return '/images/products/101.svg'
  return '/images/products/generic.svg'
}

export function productImageUrl(product: Product) {
  const productWithImage = product as Product & {
    imagem_url?: string | null
    image_url?: string | null
  }
  // Submitted product photographs take precedence for matched catalog items.
  // Other products keep their API image and existing illustrative fallback.
  return (
    localCatalogImageUrl(product) ||
    productWithImage.imagem_url ||
    productWithImage.image_url ||
    productFallbackImageUrl(product)
  )
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
