const API = process.env.REACT_APP_API_URL;

export async function listApifyActors(): Promise<any[]> {
  const res = await fetch(`${API}/api/apify/actors`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function runApifyActor(actorId: string, input: any): Promise<any> {
  const res = await fetch(`${API}/api/apify/actors/${actorId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input)
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function listVapiAssistants(): Promise<any[]> {
  const res = await fetch(`${API}/api/vapi/assistants`);
  if (!res.ok) throw new Error(res.statusText);
  const { assistants } = await res.json();
  return assistants;
}

export async function makeVapiCall(
  assistantId: string,
  phone_number: string,
  initial_message?: string
): Promise<any> {
  const res = await fetch(`${API}/api/vapi/call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ assistant_id: assistantId, phone_number, initial_message })
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function scheduleVapiCall(
  assistantId: string,
  phone_number: string,
  schedule_time: string,
  initial_message?: string
): Promise<any> {
  const res = await fetch(`${API}/api/vapi/schedule_call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ assistant_id: assistantId, phone_number, schedule_time, initial_message })
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function getVapiCallStatus(callId: string): Promise<any> {
  const res = await fetch(`${API}/api/vapi/call_status/${callId}`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function generateArcadeUploadUrl(contentType: string): Promise<any> {
  const res = await fetch(
    `${API}/api/arcade/generate-upload-url?content_type=${encodeURIComponent(contentType)}`
  );
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function createArcadeSession(
  uploadId: string,
  title: string,
  events: any[]
): Promise<any> {
  const res = await fetch(`${API}/api/arcade/arcades`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uploadId, title, events })
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function translateText(
  params: { text: string; target_lang: string; source_lang?: string }
): Promise<any> {
  const res = await fetch(`${API}/api/localization/translate_text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function analyzeTrends(
  params: { product_category: string; timeframe: string }
): Promise<any> {
  const res = await fetch(`${API}/api/market_research/trends`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}
