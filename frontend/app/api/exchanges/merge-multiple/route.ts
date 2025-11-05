import { NextResponse, NextRequest } from 'next/server';

const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.FASTAPI_BASE_URL || "http://localhost:8000";

interface MergeRequest {
  exchange_ids: number[];
}

export async function POST(request: NextRequest) {
  let requestBody: MergeRequest;

  try {
    requestBody = await request.json();
  } catch (error) {
    console.error("[BFF POST /api/exchanges/merge-multiple] Error parsing request body:", error);
    return NextResponse.json({ error: 'Invalid request body, expected { exchange_ids: number[] }' }, { status: 400 });
  }

  const { exchange_ids } = requestBody;

  if (!exchange_ids || !Array.isArray(exchange_ids) || exchange_ids.length < 2) {
    return NextResponse.json({ error: 'Missing, invalid, or insufficient exchange_ids. At least two are required.' }, { status: 400 });
  }
  if (!exchange_ids.every(id => typeof id === 'number')) {
    return NextResponse.json({ error: 'All exchange_ids must be numbers.' }, { status: 400 });
  }

  console.log(`[BFF POST /api/exchanges/merge-multiple] Attempting to merge exchanges with IDs: ${exchange_ids.join(', ')}`);

  try {
    const backendUrl = `${FASTAPI_BASE_URL}/api/exchanges/merge`;
    console.log(`[BFF POST /api/exchanges/merge-multiple] Calling backend: ${backendUrl}`);

    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ exchange_ids: exchange_ids }), // Backend expects this body
    });

    const responseData = await backendResponse.json(); // Always try to parse JSON for consistent error/success handling

    if (!backendResponse.ok) {
      console.error(`[BFF POST /api/exchanges/merge-multiple] Backend error: ${backendResponse.status}`, responseData);
      return NextResponse.json(responseData.detail || responseData, { status: backendResponse.status });
    }
    
    console.log(`[BFF POST /api/exchanges/merge-multiple] Successfully merged exchanges. Backend response:`, responseData);
    return NextResponse.json(responseData); // Forward backend success response (e.g., { message, target_exchange_id })

  } catch (error: any) {
    console.error(`[BFF POST /api/exchanges/merge-multiple] Error processing merge request for exchange_ids ${exchange_ids.join(', ')}:`, error);
    return NextResponse.json({ error: error.message || 'Failed to merge exchanges' }, { status: 500 });
  }
} 