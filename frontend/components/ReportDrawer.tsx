"use client";
import { useState, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, X, Plus } from "lucide-react";

export default function ReportDrawer() {
  const [open, setOpen] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-[1000] rounded-full bg-[#FF6B6B] text-white p-4 shadow-lg hover:bg-[#ff8080]"
      >
        <Plus className="w-6 h-6" />
      </motion.button>

      {/* Slide-in drawer */}
      <AnimatePresence>
        {open && (
          <>
            {/* backdrop */}
            <motion.div
              onClick={() => setOpen(false)}
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[999]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />

            {/* panel */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", stiffness: 90 }}
              className="fixed top-0 right-0 h-full w-[350px] bg-white shadow-2xl z-[1001] flex flex-col p-6 overflow-y-auto"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-[#2B2B2B]">
                  Report a Plothole 🕳️
                </h2>
                <button onClick={() => setOpen(false)}>
                  <X className="w-6 h-6 text-[#555]" />
                </button>
              </div>

              {/* Upload area */}
              <label className="relative flex flex-col items-center justify-center border-2 border-dashed border-[#FFD6A5] rounded-xl p-6 bg-[#FFF9F3] hover:bg-[#fff4e8] transition cursor-pointer">
                {!preview ? (
                  <>
                    <Upload className="w-8 h-8 text-[#FF6B6B] mb-2" />
                    <p className="text-[#2B2B2B] font-semibold">
                      Upload pothole photo
                    </p>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFile}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                  </>
                ) : (
                  <div className="flex flex-col items-center w-full">
                    <img
                      src={preview}
                      alt="preview"
                      className="w-full h-40 object-cover rounded-lg shadow"
                    />
                    <button
                      onClick={() => setPreview(null)}
                      className="mt-3 text-sm text-[#FF6B6B] underline"
                    >
                      Remove photo
                    </button>
                  </div>
                )}
              </label>

              {/* Optional description */}
              <textarea
                placeholder="Describe the location or issue..."
                className="mt-5 p-3 rounded-lg border border-[#ddd] text-sm focus:outline-none focus:ring-2 focus:ring-[#FFADAD]"
              />

              <motion.button
                whileHover={{ scale: 1.05 }}
                onClick={() => setOpen(false)}
                className="mt-6 bg-[#B9FBC0] font-bold text-[#2B2B2B] py-3 rounded-lg shadow hover:bg-[#a4e9ad] transition"
              >
                Submit
              </motion.button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
