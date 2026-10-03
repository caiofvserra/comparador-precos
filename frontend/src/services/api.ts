export type Product = {
  id: number
  nome: string
  marca?: string | null
  categorias?: string[]
  preco_minimo?: string | null
  preco_maximo?: string | null
}
export type Supermarket = { id: number; nome: string }
export type Price = {
  supermercado: Supermarket
  disponivel: boolean
  valor: string | null
  data_hora_coleta: string | null
  url_fonte: string | null
}
export type Comparison = { produto: Product; precos: Price[] }
export type HistoryEntry = {
  supermercado: Supermarket
  valor: string
  data_hora_coleta: string
  url_fonte: string
}
export type ProductHistory = { produto: Product; historico: HistoryEntry[] }
export type ListRequest = { itens: { produto_id: number; quantidade: number }[] }
export type SimulatedItem = {
  produto_id: number
  quantidade: number
  valor_unitario: string
  subtotal: string
}
export type SupermarketResult = {
  supermercado: Supermarket
  status: 'completo' | 'incompleto'
  itens_encontrados: number
  itens: SimulatedItem[]
  total: string
  itens_ausentes: number[]
}
export type Simulation = { total_itens: number; supermercados: SupermarketResult[] }

export const isDemoData = !import.meta.env.VITE_API_URL

const supermarkets: Supermarket[] = [
  { id: 1, nome: 'Atacadão' },
  { id: 2, nome: 'Savegnago' },
  { id: 3, nome: 'Carrefour' },
]

const products: Product[] = [
  { id: 101, nome: 'Arroz integral 5 kg', marca: 'Camil', categorias: ['Alimentos', 'Mercearia'] },
  {
    id: 205,
    nome: 'Azeite extravirgem 500 ml',
    marca: 'Gallo',
    categorias: ['Alimentos', 'Mercearia', 'Vegano'],
  },
  {
    id: 309,
    nome: 'Café tradicional 500 g',
    marca: 'Melitta',
    categorias: ['Alimentos', 'Mercearia', 'Vegano'],
  },
  {
    id: 412,
    nome: 'Leite integral 1 L',
    marca: 'Piracanjuba',
    categorias: ['Bebidas', 'Laticínios'],
  },
  { id: 518, nome: 'Pão italiano 1 kg', marca: null, categorias: ['Alimentos', 'Padaria'] },
  {
    id: 623,
    nome: 'Banana nanica 1 kg',
    marca: null,
    categorias: ['Alimentos', 'Hortifruti', 'Vegano'],
  },
  { id: 744, nome: 'Detergente líquido 500 ml', marca: 'Ypê', categorias: ['Limpeza'] },
  { id: 855, nome: 'Sabonete glicerinado 90 g', marca: 'Dove', categorias: ['Higiene pessoal'] },
  { id: 966, nome: 'Refrigerante cola 2 L', marca: 'Coca-Cola', categorias: ['Bebidas'] },
  {
    id: 1077,
    nome: 'Leite desnatado 1 L',
    marca: 'Itambé',
    categorias: ['Bebidas', 'Laticínios', 'Light', 'Diet'],
  },
]

const sourceUrls = [
  'https://www.atacadao.com.br/',
  'https://www.savegnago.com.br/',
  'https://mercado.carrefour.com.br/',
]

const collectedAt = '2026-10-02T10:30:00-03:00'
const demoHistoryDates = [
  '2026-07-10T10:30:00-03:00',
  '2026-08-07T10:30:00-03:00',
  '2026-08-28T10:30:00-03:00',
  '2026-09-18T10:30:00-03:00',
  collectedAt,
]
const demoHistoryPriceOffsetsInCents = [-60, -25, 35, -15, 0]

const createComparison = (product: Product, values: (string | null)[]): Comparison => ({
  produto: product,
  precos: supermarkets.map((supermercado, index) => {
    const valor = values[index] ?? null
    return {
      supermercado,
      disponivel: valor !== null,
      valor,
      data_hora_coleta: valor ? collectedAt : null,
      url_fonte: valor ? sourceUrls[index]! : null,
    }
  }),
})

const comparisons: Record<number, Comparison> = Object.fromEntries(
  [
    createComparison(products[0]!, ['24.90', '26.49', null]),
    createComparison(products[1]!, ['34.90', null, '32.50']),
    createComparison(products[2]!, ['19.90', '18.49', '21.90']),
    createComparison(products[3]!, ['5.19', '4.89', '5.49']),
    createComparison(products[4]!, [null, '14.90', '16.50']),
    createComparison(products[5]!, ['6.49', '5.99', '7.20']),
    createComparison(products[6]!, ['2.79', '2.49', null]),
    createComparison(products[7]!, ['4.49', '5.19', '4.89']),
    createComparison(products[8]!, ['9.49', '8.99', '10.29']),
    createComparison(products[9]!, ['4.79', '4.59', '5.19']),
  ].map((comparison) => [comparison.produto.id, comparison]),
)

const apiBase = import.meta.env.VITE_API_URL?.replace(/\/+$/, '')

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!response.ok) throw new Error(`Não foi possível carregar os dados (${response.status}).`)
  return response.json() as Promise<T>
}

export async function getProducts(query = ''): Promise<Product[]> {
  const normalizedQuery = query.trim().toLocaleLowerCase('pt-BR')
  if (!isDemoData) {
    const queryString = normalizedQuery ? `?q=${encodeURIComponent(normalizedQuery)}` : ''
    return request(`/api/v1/produtos/${queryString}`)
  }
  const matches = products
    .filter((product) =>
      `${product.nome} ${product.marca ?? ''}`.toLocaleLowerCase('pt-BR').includes(normalizedQuery),
    )
    .sort((first, second) => first.nome.localeCompare(second.nome, 'pt-BR'))
  return matches.map((product) => {
    const prices = (comparisons[product.id]?.precos ?? [])
      .filter((price) => price.disponivel && price.valor !== null)
      .map((price) => Number(price.valor))
    return {
      ...product,
      preco_minimo: prices.length ? Math.min(...prices).toFixed(2) : null,
      preco_maximo: prices.length ? Math.max(...prices).toFixed(2) : null,
    }
  })
}

export async function getSupermarkets(): Promise<Supermarket[]> {
  if (!isDemoData) return request('/api/v1/supermercados/')
  return supermarkets
}

export async function getComparison(productId: number): Promise<Comparison> {
  if (!isDemoData) return request(`/api/v1/produtos/${productId}/comparacao/`)
  const comparison = comparisons[productId]
  if (!comparison) throw new Error('Produto sem dados de comparação.')
  return comparison
}

export async function getProductHistory(
  productId: number,
  supermarketId?: number,
): Promise<ProductHistory> {
  if (!isDemoData) {
    const query = supermarketId ? `?supermercado_id=${supermarketId}` : ''
    return request(`/api/v1/produtos/${productId}/historico/${query}`)
  }

  const comparison = comparisons[productId]
  if (!comparison) throw new Error('Produto sem histórico disponível.')
  const availableValues = comparison.precos
    .map((price) => (price.valor === null ? null : Math.round(Number(price.valor) * 100)))
    .filter((value): value is number => value !== null)
  const referenceValue =
    availableValues.reduce((total, value) => total + value, 0) / availableValues.length
  const historico = comparison.precos
    .filter((price) => !supermarketId || price.supermercado.id === supermarketId)
    .flatMap((price) => {
      const currentValue =
        price.valor === null ? Math.round(referenceValue) : Math.round(Number(price.valor) * 100)
      return demoHistoryDates.map((data_hora_coleta, index) => ({
        supermercado: price.supermercado,
        valor: ((currentValue + demoHistoryPriceOffsetsInCents[index]!) / 100).toFixed(2),
        data_hora_coleta,
        url_fonte: price.url_fonte ?? sourceUrls[price.supermercado.id - 1]!,
      }))
    })
    .sort((first, second) => first.data_hora_coleta.localeCompare(second.data_hora_coleta))
  return { produto: comparison.produto, historico }
}

export async function simulateList(payload: ListRequest): Promise<Simulation> {
  if (!isDemoData) {
    return request('/api/v1/listas/simular/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  const supermercadoResults = supermarkets.map((supermercado): SupermarketResult => {
    const itens: SimulatedItem[] = []
    const itensAusentes: number[] = []
    let totalCentavos = 0

    for (const item of payload.itens) {
      const price = comparisons[item.produto_id]?.precos.find(
        (offer) => offer.supermercado.id === supermercado.id,
      )
      if (!price?.valor) {
        itensAusentes.push(item.produto_id)
        continue
      }
      const unitCentavos = Math.round(Number(price.valor) * 100)
      const subtotalCentavos = unitCentavos * item.quantidade
      totalCentavos += subtotalCentavos
      itens.push({
        produto_id: item.produto_id,
        quantidade: item.quantidade,
        valor_unitario: (unitCentavos / 100).toFixed(2),
        subtotal: (subtotalCentavos / 100).toFixed(2),
      })
    }

    return {
      supermercado,
      status: itensAusentes.length ? 'incompleto' : 'completo',
      itens_encontrados: itens.length,
      itens,
      total: (totalCentavos / 100).toFixed(2),
      itens_ausentes: itensAusentes,
    }
  })

  return { total_itens: payload.itens.length, supermercados: supermercadoResults }
}
