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

    const imageUrl = `${process.env.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/public/plothole-uploads/${uploaded.path}`;

    // For testing with local images
    const useTestImage = true; // Set to false to use the uploaded image
    const testImageName = "pothole1.webp"; // or "pothole2.webp"
    
    const requestBody = useTestImage 
      ? JSON.stringify({ 
          image_path: testImageName, 
          is_test: true 
        })
      : JSON.stringify({ 
          image_path: imageUrl, 
          is_test: false 
        });

    console.log("Sending request to analyze image:", requestBody);
    
    const analyzeRes = await fetch(
      `${process.env.NEXT_PUBLIC_FLASK_API_URL || "http://127.0.0.1:3001"}/api/analyze`, 
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: requestBody,
      }
    );

    if (!analyzeRes.ok) {
      const text = await analyzeRes.text();
      console.error("Model error:", text);
      throw new Error("Python model failed");
    }

    const response = await analyzeRes.json();
    const modelData = response.data || response; // Handle both response formats

    if(modelData.pothole) {
      console.log("PLOTHOLE DETECTED");
      try {
        // Call Python backend to add to blocked_edges_set
        await fetch(`${process.env.FLASK_API_URL || "http://127.0.0.1:3001"}/api/add_blocked_edge`, {
          method: "POST", // you should change Flask endpoint to accept POST
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ latitude: lat, longitude: lng }),
        });
      } catch (err) {
          console.error("Failed to update blocked_edges_set:", err);
      }
    }

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
    console.error("Error in /api/reports:", err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
