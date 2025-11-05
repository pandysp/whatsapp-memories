import Link from 'next/link';

// Define the expected structure of an Exchange detail
// This should match the ExchangeDetailResponse from the backend api_models
interface Message {
  date?: string | null;
  time?: string | null;
  person?: string | null;
  quote?: string | null;
}

interface ExchangeDetail {
  id: number;
  messages: Message[];
}

async function getExchangeDetail(id: string): Promise<ExchangeDetail | null> {
  try {
    // Call the BFF API route instead of the direct backend URL
    const res = await fetch(`/api/exchanges/${id}`, {
      cache: 'no-store', // For development. Adjust for production.
    });

    // The BFF route should ideally return a structured error or a 404 directly
    if (res.status === 404) {
      console.log(`[ExchangeDetailPage] BFF returned 404 for exchangeId: ${id}`);
      return null; // Exchange not found
    }

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ message: `Failed to fetch exchange detail: ${res.status} ${res.statusText}` }));
      console.error(`[ExchangeDetailPage] Failed to fetch exchange detail from BFF: ${res.status}`, errorData);
      // We could potentially display errorData.error to the user if the BFF provides a user-friendly message
      return null; // Or throw an error to be caught by an error boundary
    }
    return res.json();
  } catch (error) {
    console.error('[ExchangeDetailPage] Error fetching exchange detail:', error);
    return null; // Or throw an error
  }
}

interface ExchangeDetailPageProps {
  params: Promise<{
    exchangeId: string;
  }>;
}

export default async function ExchangeDetailPage({ params }: ExchangeDetailPageProps) {
  const { exchangeId } = await params;
  const exchange = await getExchangeDetail(exchangeId);

  if (!exchange) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Exchange Not Found</h1>
        <p>The exchange you are looking for does not exist.</p>
        <Link href="/exchanges" className="text-blue-500 hover:underline mt-4 inline-block">
          &larr; Back to all exchanges
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <Link href="/exchanges" className="text-blue-500 hover:underline mb-4 inline-block">
        &larr; Back to all exchanges
      </Link>
      <h1 className="text-3xl font-bold mb-6">Exchange ID: {exchange.id}</h1>
      
      {exchange.messages.length === 0 ? (
        <p>This exchange has no messages.</p>
      ) : (
        <div className="space-y-3">
          {exchange.messages.map((message, index) => (
            <div key={index} className="p-3 border rounded-md bg-gray-50 shadow-sm">
              <p className="font-semibold text-gray-700">{message.person || 'Unknown Person'}</p>
              <p className="text-gray-800 whitespace-pre-wrap">{message.quote || ''}</p>
              <p className="text-xs text-gray-400 mt-1">
                {message.date || ''} {message.time || ''}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Optional: If you have a lot of exchange IDs and want to statically generate them at build time
// export async function generateStaticParams() {
//   // Fetch all exchange IDs from your API
//   const res = await fetch('http://localhost:8000/api/exchanges/');
//   const exchanges: { id: number }[] = await res.json(); // Assuming API returns {id: ...}[]
 
//   return exchanges.map((exchange) => ({
//     exchangeId: exchange.id.toString(),
//   }));
// } 