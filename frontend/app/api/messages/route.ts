import { NextResponse, NextRequest } from 'next/server';
// Remove fs and path, import kv
// import fs from 'fs/promises';
// import path from 'path';
import { kv } from '@vercel/kv';

interface Message {
  date: string;
  time: string;
  person: string;
  quote: string;
}

interface ExchangeWithSource {
    sourceFile: string;
    internalIndex: number;
    messages: Message[];
    exchange_id?: number;
}

interface KVDataStructure {
  cute_exchanges: Message[][];
}

interface PaginatedApiResponseData {
    content: {
        cute_exchanges: ExchangeWithSource[];
    },
    pagination: {
        currentPage: number;
        pageSize: number;
        totalExchanges: number;
        hasMore: boolean;
    }
}

// Interfaces for data coming from FastAPI backend
interface FastAPIMessage {
    date?: string | null;
    time?: string | null;
    person?: string | null;
    quote?: string | null;
}

interface FastAPIExchangeSummary {
    id: number; // This is the global exchange_id
    cache_key: string;
    exchange_index: number;
    first_message: FastAPIMessage | null;
}

interface FastAPIPaginationInfo {
    currentPage: number;
    pageSize: number;
    totalItems: number;
    totalPages: number; // We might not directly use totalPages in the old model
    hasMore: boolean;
}

interface FastAPIPaginatedResponse {
    items: FastAPIExchangeSummary[];
    pagination: FastAPIPaginationInfo;
}

const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.FASTAPI_BASE_URL || "http://localhost:8000";

// The sortMessagesChronologically helper is not needed here anymore, 
// as sorting is handled by the FastAPI backend.

export async function GET(request: NextRequest) {
  console.log(`[BFF GET /api/messages] Request received.`);

  const { searchParams } = request.nextUrl;
  const page = searchParams.get('page') || '1';
  const pageSize = searchParams.get('pageSize') || '20';
  // Default sort order for FastAPI, can be made configurable if needed
  const sortBy = 'asc'; 

  console.log(`[BFF GET /api/messages] Requesting page=${page}, pageSize=${pageSize}, sort=${sortBy} from FastAPI.`);

  try {
    const fastapiResponse = await fetch(
        `${FASTAPI_BASE_URL}/api/exchanges/?page=${page}&page_size=${pageSize}&sort_by_first_message_date=${sortBy}`,
        {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
            cache: 'no-store' // Or configure as needed
        }
    );

    if (!fastapiResponse.ok) {
        const errorBody = await fastapiResponse.text();
        console.error(`[BFF GET /api/messages] FastAPI error: ${fastapiResponse.status}`, errorBody);
        throw new Error(`FastAPI request failed with status ${fastapiResponse.status}`);
    }

    const fastapiData: FastAPIPaginatedResponse = await fastapiResponse.json();

    // Transform FastAPI data to the structure page.tsx expects
    const transformedExchanges: ExchangeWithSource[] = fastapiData.items.map(item => {
        const messagesArray: Message[] = [];
        if (item.first_message) {
            messagesArray.push({
                date: item.first_message.date || '',
                time: item.first_message.time || '',
                person: item.first_message.person || 'Unknown',
                quote: item.first_message.quote || ''
            });
        }
        return {
            sourceFile: item.cache_key,       // Map cache_key to sourceFile
            internalIndex: item.exchange_index, // Map exchange_index to internalIndex
            messages: messagesArray,             // Embed the first message in a messages array
            exchange_id: item.id              // Pass through the global exchange_id
        };
    });
    
    // The old BFF layer performed its own sorting after fetching all data.
    // Now, FastAPI handles sorting. If the old frontend relied on a specific client-side sort
    // or secondary sort after this fetch, that behavior might change slightly.
    // For now, we assume FastAPI's sorting is what we need.

    const responseData: PaginatedApiResponseData = {
        content: {
            cute_exchanges: transformedExchanges
        },
        pagination: {
            currentPage: fastapiData.pagination.currentPage,
            pageSize: fastapiData.pagination.pageSize,
            totalExchanges: fastapiData.pagination.totalItems, // Map totalItems to totalExchanges
            hasMore: fastapiData.pagination.hasMore
        }
    };

    console.log(`[BFF GET /api/messages] Successfully transformed data. Returning ${transformedExchanges.length} exchanges for page ${page}. HasMore: ${fastapiData.pagination.hasMore}`);
    return NextResponse.json(responseData);

  } catch (error: any) {
    console.error('[BFF GET /api/messages] Error processing request:', error);
    // Ensure a compatible error structure or a generic one for page.tsx
    const responseData: PaginatedApiResponseData = {
        content: { cute_exchanges: [] },
        pagination: { currentPage: Number(page), pageSize: Number(pageSize), totalExchanges: 0, hasMore: false }
    };
    // Optionally, include an error field if page.tsx can handle it, otherwise just empty data
    // return NextResponse.json({ ...responseData, error: error.message || 'Failed to load messages' }, { status: 500 });
    return NextResponse.json(responseData, { status: 500 }); // Return empty valid structure on error
  }
} 