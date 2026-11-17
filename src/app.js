const surahInput = document.getElementById("surah");
const reciterInput = document.getElementById("reciter");
const ayahInput = document.getElementById("ayah");
const previewArea = document.getElementById("previewArea");

document.getElementById("preview").addEventListener("click", () => {
  const surah = surahInput.value.trim();
  const reciter = reciterInput.value.trim();
  const ayat = ayahInput.value.trim();

  if (!surah && !reciter && !ayat) {
    previewArea.textContent = "أدخل معلومات السورة والآيات أولاً.";
    return;
  }

  previewArea.replaceChildren();
  const title = document.createElement("p");
  title.className = "preview-title";
  title.textContent = surah || "سورة القرآن الكريم";
  const reader = document.createElement("p");
  reader.textContent = reciter ? "القارئ: " + reciter : "القارئ: لم يُحدّد بعد";
  const text = document.createElement("p");
  text.textContent = ayat || "لم يُضف نص الآيات بعد.";
  previewArea.append(title, reader, text);
});

document.getElementById("clear").addEventListener("click", () => {
  surahInput.value = "";
  reciterInput.value = "";
  ayahInput.value = "";
  previewArea.innerHTML = '<p class="placeholder">ستظهر معاينة معلومات الفيديو هنا.</p>';
});
