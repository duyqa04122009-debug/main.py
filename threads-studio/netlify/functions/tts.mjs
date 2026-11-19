export default async (req) => {
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "Method not allowed" }), { status: 405, headers: { "content-type": "application/json" } });
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) return new Response(JSON.stringify({ error: "Chưa cấu hình ELEVENLABS_API_KEY trong Netlify." }), { status: 500, headers: { "content-type": "application/json" } });
  try {
    const { text, voiceId, speed } = await req.json();
    if (!text || !String(text).trim()) return new Response(JSON.stringify({ error: "Vui lòng nhập nội dung cần đọc." }), { status: 400, headers: { "content-type": "application/json" } });
    if (String(text).length > 4500) return new Response(JSON.stringify({ error: "Giới hạn 4.500 ký tự mỗi lần tạo." }), { status: 400, headers: { "content-type": "application/json" } });
    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId || "21m00Tcm4TlvDq8ikWAM"}`, {
      method: "POST",
      headers: { "xi-api-key": apiKey, "Content-Type": "application/json", "Accept": "audio/mpeg" },
      body: JSON.stringify({ text: String(text), model_id: "eleven_multilingual_v2", voice_settings: { stability: 0.48, similarity_boost: 0.76, style: 0.15, use_speaker_boost: true, speed: Math.min(1.2, Math.max(0.7, Number(speed) || 1)) } })
    });
    if (!response.ok) return new Response(JSON.stringify({ error: `ElevenLabs trả về lỗi (${response.status}). Kiểm tra API key, hạn mức và Voice ID.` }), { status: response.status, headers: { "content-type": "application/json" } });
    return new Response(response.body, { status: 200, headers: { "Content-Type": "audio/mpeg", "Cache-Control": "no-store" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message || "Không thể tạo giọng đọc." }), { status: 500, headers: { "content-type": "application/json" } });
  }
};