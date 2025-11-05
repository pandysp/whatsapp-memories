import { NextResponse, NextRequest } from 'next/server';

// This should match the structure expected by ExchangeDetailPage
// and the one returned by the FastAPI backend /api/exchanges/{id}
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

const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.FASTAPI_BASE_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ exchangeId: string }> }
) {
  const { exchangeId } = await params;
  console.log(`[BFF GET /api/exchanges/${exchangeId}] Request received.`);

  if (!exchangeId) {
    console.log(`[BFF GET /api/exchanges/...] Error: exchangeId is missing.`);
    return NextResponse.json({ error: 'exchangeId is required' }, { status: 400 });
  }

  try {
    const backendUrl = `${FASTAPI_BASE_URL}/api/exchanges/${exchangeId}`;
    console.log(`[BFF GET /api/exchanges/${exchangeId}] Fetching data from backend: ${backendUrl}`);
    
    const fastapiResponse = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store', // Or configure as needed, consistent with page.tsx for now
    });

    if (!fastapiResponse.ok) {
      // If backend returns 404, we propagate it
      if (fastapiResponse.status === 404) {
        console.log(`[BFF GET /api/exchanges/${exchangeId}] Backend returned 404. Exchange not found.`);
        return NextResponse.json({ error: 'Exchange not found' }, { status: 404 });
      }
      const errorBody = await fastapiResponse.text();
      console.error(`[BFF GET /api/exchanges/${exchangeId}] FastAPI error: ${fastapiResponse.status}`, errorBody);
      throw new Error(`FastAPI request failed with status ${fastapiResponse.status}`);
    }

    const exchangeDetail: ExchangeDetail = await fastapiResponse.json();
    
    console.log(`[BFF GET /api/exchanges/${exchangeId}] Successfully fetched data from backend.`);
    return NextResponse.json(exchangeDetail);

  } catch (error: any) {
    console.error(`[BFF GET /api/exchanges/${exchangeId}] Error processing request:`, error);
    // Return a generic error, or specific if known (like the 404 above)
    return NextResponse.json({ error: error.message || 'Failed to load exchange details' }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ exchangeId: string }> }
) {
  const { exchangeId } = await params;
  console.log(`[BFF DELETE /api/exchanges/${exchangeId}] Request received.`);

  if (!exchangeId) {
    console.log(`[BFF DELETE /api/exchanges/...] Error: exchangeId is missing.`);
    return NextResponse.json({ error: 'exchangeId is required' }, { status: 400 });
  }

  try {
    const backendUrl = `${FASTAPI_BASE_URL}/api/exchanges/${exchangeId}`;
    console.log(`[BFF DELETE /api/exchanges/${exchangeId}] Forwarding DELETE request to backend: ${backendUrl}`);
    
    const fastapiResponse = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        // No Content-Type needed for a typical DELETE with ID in path and no body
        'Accept': 'application/json', // Or */* if backend might not return JSON on success (e.g. just 204)
      },
    });

    // Backend returns 204 No Content on successful deletion, and 404 if not found.
    if (fastapiResponse.status === 204) {
      console.log(`[BFF DELETE /api/exchanges/${exchangeId}] Backend confirmed deletion (204).`);
      return new NextResponse(null, { status: 204 }); // Propagate 204
    }
    
    if (fastapiResponse.status === 404) {
      console.log(`[BFF DELETE /api/exchanges/${exchangeId}] Backend returned 404. Exchange not found for deletion.`);
      return NextResponse.json({ error: 'Exchange not found for deletion' }, { status: 404 });
    }

    // Handle other unexpected errors from backend
    if (!fastapiResponse.ok) {
      const errorBody = await fastapiResponse.text();
      console.error(`[BFF DELETE /api/exchanges/${exchangeId}] FastAPI error on DELETE: ${fastapiResponse.status}`, errorBody);
      throw new Error(`FastAPI DELETE request failed with status ${fastapiResponse.status}`);
    }

    // Should not be reached if backend adheres to 204 on success
    console.log(`[BFF DELETE /api/exchanges/${exchangeId}] Backend returned unexpected status: ${fastapiResponse.status}`);
    return NextResponse.json({ message: 'Delete operation completed with unexpected status' }, { status: fastapiResponse.status });

  } catch (error: any) {
    console.error(`[BFF DELETE /api/exchanges/${exchangeId}] Error processing DELETE request:`, error);
    return NextResponse.json({ error: error.message || 'Failed to delete exchange' }, { status: 500 });
  }
} 