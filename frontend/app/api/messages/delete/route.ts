import { NextResponse, NextRequest } from 'next/server';

const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.FASTAPI_BASE_URL || "http://localhost:8000";

interface DeleteMessagesRequest {
  message_ids: number[];
}

export async function POST(request: NextRequest) {
  let requestBody: DeleteMessagesRequest;

  try {
    requestBody = await request.json();
  } catch (error) {
    console.error("[BFF POST /api/messages/delete] Error parsing request body:", error);
    return NextResponse.json({ error: 'Invalid request body, expected { message_ids: number[] }' }, { status: 400 });
  }

  const { message_ids } = requestBody;

  if (!message_ids || !Array.isArray(message_ids)) { // Could also check for empty array if backend requires non-empty
    return NextResponse.json({ error: 'Missing or invalid message_ids in request body' }, { status: 400 });
  }
  // Optional: Check if all IDs are numbers if not strictly enforced by TS/Pydantic on backend
  // if (!message_ids.every(id => typeof id === 'number')) {
  //   return NextResponse.json({ error: 'All message_ids must be numbers.' }, { status: 400 });
  // }

  console.log(`[BFF POST /api/messages/delete] Attempting to delete messages with IDs: ${message_ids.join(', ')}`);

  try {
    const backendUrl = `${FASTAPI_BASE_URL}/api/messages`; // Backend uses DELETE here
    console.log(`[BFF POST /api/messages/delete] Calling backend: DELETE ${backendUrl}`);

    const backendResponse = await fetch(backendUrl, {
      method: 'DELETE', // Align with the backend endpoint method
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ message_ids: message_ids }), // Backend expects this body for its DELETE
    });

    const responseData = await backendResponse.json(); // Always try to parse JSON

    if (!backendResponse.ok) {
      console.error(`[BFF POST /api/messages/delete] Backend error: ${backendResponse.status}`, responseData);
      // Forward backend's error detail if available, otherwise a generic message
      return NextResponse.json(responseData.detail || responseData, { status: backendResponse.status });
    }
    
    console.log(`[BFF POST /api/messages/delete] Successfully deleted messages. Backend response:`, responseData);
    // Forward backend success response (e.g., { deleted_count: number })
    return NextResponse.json(responseData);

  } catch (error: any) {
    console.error(`[BFF POST /api/messages/delete] Error processing delete messages request for IDs ${message_ids.join(', ')}:`, error);
    return NextResponse.json({ error: error.message || 'Failed to delete messages' }, { status: 500 });
  }
} 