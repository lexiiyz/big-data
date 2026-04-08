// TODO: Replace with your actual n8n Webhook URL
// If using Android emulator to reach localhost, use http://10.0.2.2:5678/webhook-test/chat
// Untuk mengakses dari HP fisik melalui Expo Go, ganti 'localhost' dengan IP Address laptop/PC Anda.
const WEBHOOK_URL = 'http://10.57.14.21:5678/webhook/chat';

export async function sendChatMessage(text: string): Promise<string> {
  const response = await fetch(WEBHOOK_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ chatInput: text }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json().catch(() => null);

  if (data && data.output) {
    return data.output;
  } else if (data && data.content) {
    return data.content;
  } else if (typeof data === 'string') {
    return data;
  } else if (data) {
    return JSON.stringify(data);
  } else {
    return await response.text();
  }
}
