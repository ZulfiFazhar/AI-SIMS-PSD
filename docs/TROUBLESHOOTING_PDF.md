# Troubleshooting PDF Parser & Proposal Classification

## Common Issues

### 1. "Gagal mengekstrak teks dari PDF"

**Error Message:**

```json
{
  "status": "failed",
  "message": "Gagal mengekstrak teks dari PDF. Kemungkinan penyebab: 1) PDF tidak dapat diakses dari URL, 2) PDF kosong atau corrupt, 3) Format PDF tidak didukung.",
  "data": null
}
```

**Kemungkinan Penyebab:**

#### A. URL PDF Tidak Valid atau Tidak Dapat Diakses

- PDF disimpan di bucket private tanpa public access
- URL expired (signed URL sudah kadaluarsa)
- Firewall atau CORS blocking request

**Solusi:**

```bash
# Test URL dengan curl
curl -I "https://your-pdf-url.pdf"

# Harus return status 200 OK
# Check jika ada redirect atau error
```

#### B. PDF Kosong atau Corrupt

- File PDF rusak saat upload
- Upload tidak selesai dengan sempurna
- PDF terenkripsi atau password-protected

**Solusi:**

1. Download PDF manual dan buka di PDF reader
2. Verify file size > 0 bytes
3. Re-upload PDF jika corrupt

#### C. PDF Berupa Gambar/Scan (Tidak Ada Text Layer)

- PDF hasil scan tanpa OCR
- PDF berupa image-only

**Solusi:**

1. Pastikan PDF memiliki text layer (bisa copy-paste text)
2. Jika PDF adalah scan, lakukan OCR dulu
3. Re-create PDF dari Word/Google Docs dengan text layer

#### D. Format PDF Tidak Standar

- PDF versi lama atau custom format
- PDF dengan encoding khusus

**Solusi:**

1. Convert PDF ke versi standar (PDF 1.4+)
2. Re-export dari sumber asli

### 2. "Teks proposal terlalu pendek"

**Error Message:**

```json
{
  "status": "failed",
  "message": "Teks proposal terlalu pendek. Minimal 50 karakter diperlukan.",
  "data": null
}
```

**Kemungkinan Penyebab:**

#### A. Section Extraction Gagal (Regex Tidak Match)

Parser menggunakan regex untuk find sections. Jika format heading berbeda, sections tidak ter-extract.

**Expected Format:**

```
1.1 Latar Belakang Usaha
2.1 Noble Purpose
2.2 Identifikasi Konsumen
2.3 Produk Inovatif
2.4 Strategi Pemasaran
2.5 Sumber Daya
3.1 Laporan/Proyeksi Keuangan
3.2 Rencana Anggaran Belanja
```

**Variasi yang Akan Di-match:**

- "1.1 Latar Belakang Usaha"
- "1.1 Latar Belakang Usaha" (extra spaces)
- "1.1 LATAR BELAKANG USAHA" (uppercase)

**Variasi yang TIDAK akan di-match:**

- "1.1. Latar Belakang Usaha" (titik tambahan)
- "A. Latar Belakang Usaha" (bukan angka)
- "Latar Belakang Usaha" (tanpa numbering)

**Solusi:**

1. Pastikan heading menggunakan format yang benar
2. Check log untuk melihat berapa sections yang ter-detect:
   ```
   INFO - Found X section headings in PDF
   ```
3. Jika 0 sections found, berarti format heading berbeda

#### B. PDF Hanya Berisi Halaman Sampul/ToC

- Proposal hanya cover dan daftar isi
- Content belum ada

**Solusi:**

1. Ensure PDF includes actual content pages
2. Minimum 2-3 halaman dengan content

### 3. Sections Tidak Ter-extract

**Log Message:**

```
WARNING - No section headings found in PDF text
WARNING - Section extraction resulted in insufficient text (0 chars). Falling back to full PDF text.
```

**Diagnosis:**

#### Step 1: Check Log untuk Detail

Look for these log messages:

```
INFO - Extracted X characters from PDF
INFO - PDF has X pages
DEBUG - Extracted X chars from page 1
INFO - Found X section headings in PDF
```

#### Step 2: Manual Check Format

Download PDF dan check:

1. Apakah ada numbering 1.1, 2.1, 2.2, dst?
2. Apakah ada extra karakter (titik, kurung)?
3. Apakah spacing konsisten?

#### Step 3: Test Regex

```python
import re

# Your PDF text
text = """
1.1 Latar Belakang Usaha
Isi latar belakang...

2.1 Noble Purpose
Isi noble purpose...
"""

# Test pattern
pattern = r"1\.1\s+Latar\s+Belakang\s+Usaha"
match = re.search(pattern, text, re.IGNORECASE)
print(match)  # Should not be None
```

**Solusi:**

1. **Fallback Aktif**: Parser otomatis fallback ke full text jika sections < 100 chars
2. **Fix Template**: Update proposal template untuk konsisten dengan format
3. **Custom Regex**: Contact developer untuk adjust regex pattern jika format berbeda

### 4. Model Loading Error

**Error Message:**

```
FileNotFoundError: Model tidak ditemukan di app/ml/indobert_full_proposal_finetuned/
```

**Solusi:**

1. Ensure model directory exists
2. Run notebook `4_Finetuning.ipynb` untuk train model
3. Copy model folder ke `app/ml/`

### 5. Out of Memory

**Error Message:**

```
CUDA out of memory
RuntimeError: CUDA out of memory
```

**Solusi:**

1. Model otomatis fallback ke CPU jika GPU tidak ada
2. Restart application untuk clear memory
3. Reduce concurrent requests

## Debugging Steps

### Step 1: Enable Debug Logging

Update `.env`:

```
LOG_LEVEL=DEBUG
```

Restart server:

```bash
uv run fastapi dev
```

### Step 2: Check Logs

Look for these patterns:

```
INFO - Classifying proposal for tenant XXXX: https://...
DEBUG - Extracting text from PDF using pdfplumber: /tmp/...
DEBUG - PDF has X pages
DEBUG - Extracted X chars from page 1
INFO - Extracted X characters from PDF
INFO - Found X section headings in PDF
DEBUG -   - 1.1 Latar Belakang Usaha at position 123
DEBUG -   - 2.1 Noble Purpose at position 456
INFO - Parsed X sections from proposal
INFO - Extracted sections from PDF. Total sections with content: X
```

### Step 3: Test PDF Manually

```python
from app.services.pdf_parser_service import pdf_parser_service
import asyncio

# Test parse
async def test():
    text = await pdf_parser_service.parse_pdf_from_url(
        "YOUR_PDF_URL",
        extract_sections=True
    )
    print(f"Extracted text length: {len(text) if text else 0}")
    print(f"Text preview: {text[:500] if text else 'None'}")

asyncio.run(test())
```

### Step 4: Test Sections Manually

```python
from app.services.pdf_parser_service import pdf_parser_service
import asyncio

async def test_sections():
    sections = await pdf_parser_service.parse_pdf_sections_from_url("YOUR_PDF_URL")

    if sections:
        for key, value in sections.items():
            print(f"{key}: {len(value)} chars")
            print(f"  Preview: {value[:100]}...")
    else:
        print("No sections found")

asyncio.run(test_sections())
```

## Best Practices

### For Frontend Developers

1. **Validate PDF before upload**

   - Check file size > 0
   - Check extension is .pdf
   - Check file is not corrupt

2. **Show upload progress**

   - Give feedback during upload
   - Show error if upload fails

3. **Handle classification errors gracefully**
   ```javascript
   if (result.status === "failed") {
     if (result.message.includes("format heading")) {
       // Show message about format requirements
     } else if (result.message.includes("tidak dapat diakses")) {
       // Suggest re-upload
     }
   }
   ```

### For Proposal Writers

1. **Use Correct Format**

   - Follow template exactly
   - Don't modify numbering
   - Use consistent spacing

2. **Ensure Content Quality**

   - Minimum 100 words per section
   - Clear and detailed descriptions
   - No lorem ipsum or placeholder text

3. **Save as PDF Properly**
   - Export from Word/Google Docs (not print to PDF)
   - Ensure text is selectable
   - Check file opens correctly

## Contact

If issue persists after trying all solutions above, contact developer with:

1. Tenant ID
2. PDF URL (if accessible)
3. Full error message
4. Logs (if available)
