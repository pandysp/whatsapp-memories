import Link from 'next/link';

// Define the expected structure of an Exchange for the frontend
// This should match the ExchangeSummaryResponse from the backend api_models
interface ExchangeSummary {
  id: number;
  first_message: {
    date?: string | null;
    time?: string | null;
    person?: string | null;
    quote?: string | null;
  } | null;
}

// Interface for a single message as returned in the messages array by /api/messages
interface BffMessage {
  date: string;
  time: string;
  person: string;
  quote: string;
}

// Interface for an exchange as returned by the /api/messages BFF route
interface BffExchange {
    sourceFile: string;
    internalIndex: number;
    messages: BffMessage[];
    exchange_id?: number; // This is the backend exchange_id
}

interface PaginatedBffResponse {
    content: {
        cute_exchanges: BffExchange[];
    },
    // We'll ignore pagination fields for now, assuming we get enough data on page 1
    // or that the page will be updated later to handle pagination.
}

async function getExchanges(): Promise<ExchangeSummary[]> {
  try {
    // Call the BFF API route /api/messages
    const res = await fetch('/api/messages', { // Using default page & pageSize from BFF
      cache: 'no-store', 
    });

    if (!res.ok) {
      console.error(`[ExchangesPage] Failed to fetch exchanges from BFF: ${res.status} ${res.statusText}`);
      return []; 
    }
    const bffData: PaginatedBffResponse = await res.json();

    // Transform BFF data to the structure ExchangesPage expects
    if (!bffData.content || !bffData.content.cute_exchanges) {
        console.error('[ExchangesPage] Invalid data structure from BFF /api/messages');
        return [];
    }

    return bffData.content.cute_exchanges.map(bffExchange => {
        const firstMessage = bffExchange.messages && bffExchange.messages.length > 0 
            ? bffExchange.messages[0] 
            : null;
        return {
            id: bffExchange.exchange_id!, // Assert exchange_id is present as it's crucial
            first_message: firstMessage ? {
                date: firstMessage.date,
                time: firstMessage.time,
                person: firstMessage.person,
                quote: firstMessage.quote,
            } : null,
        };
    }).filter(exchange => exchange.id !== undefined); // Ensure we only process exchanges with an ID

  } catch (error) {
    console.error('[ExchangesPage] Error fetching exchanges:', error);
    return [];
  }
}

export default async function ExchangesPage() {
  const exchanges = await getExchanges();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Exchanges</h1>
      {exchanges.length === 0 ? (
        <p>No exchanges found.</p>
      ) : (
        <ul className="space-y-4">
          {exchanges.map((exchange) => (
            <li key={exchange.id} className="p-4 border rounded-lg shadow-sm">
              <Link href={`/exchanges/${exchange.id}`} className="hover:underline">
                <h2 className="text-xl font-semibold">Exchange ID: {exchange.id}</h2>
              </Link>
              {exchange.first_message ? (
                <div className="mt-2 text-sm text-gray-600">
                  <p className="italic">
                    {exchange.first_message.person || 'Unknown'}: "{exchange.first_message.quote || '...'}"
                  </p>
                  <p className="text-xs text-gray-400">
                    {exchange.first_message.date} {exchange.first_message.time}
                  </p>
                </div>
              ) : (
                <p className="mt-2 text-sm text-gray-500">No preview available.</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
} 