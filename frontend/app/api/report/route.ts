import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase-server";

export const dynamic = "force-dynamic"; // ensures route works with FormData uploads

export async function POST(req: NextRequest) {
  try {
    // ---- parse multipart form ----
    const formData = await req.formData();
    const file = formData.get("file") as File | null;
    const lat = parseFloat(formData.get("lat") as string);
    const lng = parseFloat(formData.get("lng") as string);

    if (!file) {
      return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
    }

    // ---- convert uploaded file to a buffer ----
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const filePath = `uploads/${Date.now()}-${file.name}`;

    // ---- upload to Supabase Storage ----
    const { data: uploaded, error: uploadError } = await supabaseServer.storage
      .from("plothole-uploads")
      .upload(filePath, buffer, {
        contentType: file.type || "image/jpeg",
        upsert: true,
      });

    if (uploadError || !uploaded) {
      console.error("Storage upload error:", uploadError);
      throw new Error("Failed to upload to Supabase Storage");
    }

    const imageUrl = `${process.env.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/public/${uploaded.path}`;

    // ---- call Python backend model ----
    const analyzeRes = await fetch(process.env.PYTHON_API_URL || "http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_url: imageUrl }),
    });

    if (!analyzeRes.ok) {
      const text = await analyzeRes.text();
      console.error("Model error:", text);
      throw new Error("Python model failed");
    }

    const modelData = await analyzeRes.json();

    // ---- insert record into Supabase ----
    const { error: insertError } = await supabaseServer.from("reports").insert({
      image_url: imageUrl,
      lat,
      lng,
      severity: modelData.severity ?? "unknown",
      confidence: modelData.confidence ?? 0.0,
    });

    if (insertError) {
      console.error("DB insert error:", insertError);
      throw new Error("Failed to insert report");
    }

    return NextResponse.json({
      success: true,
      severity: modelData.severity,
      confidence: modelData.confidence,
      image_url: imageUrl,
    });
  } catch (err) {
    console.error("Error in /api/report:", err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
