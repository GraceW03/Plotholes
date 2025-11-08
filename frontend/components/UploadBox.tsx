"use client";
import { useState, ChangeEvent } from "react";
import { motion } from "framer-motion";
import { Upload, Image as ImageIcon } from "lucide-react";

export default function UploadBox() {
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  return (
    <motion.div
      className="flex flex-col items-center justify-center border-2 border-dashed border-[#FFD6A5] rounded-2xl p-8 bg-white/60 backdrop-blur hover:shadow-md transition cursor-pointer"
      whileHover={{ scale: 1.02 }}
    >
      {!preview ? (
        <>
          <Upload className="w-10 h-10 text-[#FF6B6B] mb-3" />
          <p className="text-[#2B2B2B] font-semibold mb-2">
            Drop your photo here or click to upload
          </p>
          <p className="text-sm text-[#777] mb-4">.jpg, .png, .heic supported</p>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="opacity-0 absolute inset-0 cursor-pointer"
          />
        </>
      ) : (
        <div className="flex flex-col items-center">
          <ImageIcon className="w-6 h-6 text-[#FF6B6B] mb-2" />
          <img
            src={preview}
            alt="preview"
            className="w-64 h-40 object-cover rounded-xl shadow"
          />
          <button
            onClick={() => setPreview(null)}
            className="mt-4 text-sm font-medium text-[#FF6B6B] underline hover:text-[#e85b5b]"
          >
            Remove photo
          </button>
        </div>
      )}
    </motion.div>
  );
}
