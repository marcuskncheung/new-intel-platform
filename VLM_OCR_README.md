# VLM OCR Feature - Important Notes

## ✅ What This Feature Does

For large scanned PDFs (>10MB) that cannot use Docling API:
1. Extracts PDF pages as images using pdf2image
2. Sends images to VLM (Qwen3-VL) for OCR text extraction
3. Processes up to 5 pages (configurable) to avoid timeout

## ⚠️ Important Limitations

### 1. **VLM API Format May Need Adjustment**
The code assumes VLM API accepts `images` parameter like this:
```json
{
  "prompt": "Extract text...",
  "images": ["data:image/jpeg;base64,ABC..."]
}
```

**If your VLM API uses a different format, you need to modify `_ocr_image_with_vlm()` function.**

### 2. **Performance Considerations**
- **Processing Time**: Each page takes ~30-60 seconds (5 pages = 2.5-5 minutes)
- **Memory Usage**: 19MB PDF → ~5-10 images × 2-3MB each = 10-30MB in memory
- **API Load**: Makes 5 API calls (one per page) to VLM

### 3. **Page Limit**
- Default: **5 pages only** (to avoid timeout)
- For 51-page PDF, only first 5 pages will be processed
- Remaining pages will not be analyzed

### 4. **Dependencies Required**
**Python packages:**
- `pdf2image==1.16.3`
- `Pillow>=10.3.0`

**System packages (in Docker):**
- `poppler-utils` (for pdf2image to work)

## 🧪 Testing Recommendations

### Test 1: Small Scanned PDF (<5 pages)
- Upload a 2-3 page scanned PDF >10MB
- Run AI analysis
- Expected: Should extract text from all pages

### Test 2: Large Scanned PDF (>10 pages)
- Upload Email 6 (51-page PDF)
- Run AI analysis
- Expected: Should extract first 5 pages only, show warning about remaining pages

### Test 3: VLM API Format
- Check VLM API response for errors like:
  - "images parameter not supported"
  - "Invalid parameter"
- If errors appear, ask IT for correct VLM vision API format

## 🔧 Configuration

To change max pages processed, edit `intelligence_ai.py`:

```python
# Line ~136: Change max_pages value
vlm_result = self.extract_pdf_images_to_vlm(file_data, filename, max_pages=10)  # Default is 5
```

## 📊 Expected Behavior

| PDF Type | Size | Method Used | Result |
|----------|------|-------------|--------|
| Text PDF | <10MB | Docling API | ✅ Full extraction |
| Text PDF | >10MB | Local (PyPDF2) | ✅ Full extraction |
| Scanned PDF | <10MB | Docling API (OCR) | ✅ Full extraction |
| Scanned PDF | >10MB | **VLM OCR** | ⚠️ First 5 pages only |

## 🚨 Potential Issues

1. **VLM API might reject image parameter** → Need to verify API format with IT
2. **Timeout on large PDFs** → Reduced to 5 pages max, lower DPI (120)
3. **Memory issues** → Added image size check (skip if >5MB)
4. **poppler not installed** → Docker build will fail if missing from Dockerfile

## ✅ Safety Measures Added

- ✅ Graceful error handling (won't crash if VLM OCR fails)
- ✅ Per-page try-catch (one page failure doesn't stop others)
- ✅ Image size validation (skip pages with images >5MB)
- ✅ Lower DPI (120 instead of 150) to reduce memory
- ✅ Lower JPEG quality (75%) to reduce API payload size
- ✅ Timeout protection (max 5 pages to avoid 10+ minute runs)

## 📝 Deployment Checklist

- [ ] `git pull` latest code
- [ ] `docker-compose build` (installs poppler-utils)
- [ ] Test with small scanned PDF first
- [ ] Check logs for VLM API errors
- [ ] If VLM API format wrong, contact IT for correct format
- [ ] Test with Email 6 (19MB scanned PDF)

