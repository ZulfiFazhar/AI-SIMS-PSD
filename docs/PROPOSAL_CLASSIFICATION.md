# Proposal Classification Service

Service untuk klasifikasi proposal bisnis menggunakan model IndoBERT yang telah di-fine-tune.

## Overview

Service ini mengimplementasikan model klasifikasi proposal berdasarkan notebook `4_Finetuning.ipynb`. Model dapat mengklasifikasi proposal menjadi dua kategori:

- **PASS**: Proposal memenuhi kriteria administrasi dan substansi
- **REJECT**: Proposal tidak memenuhi kriteria atau deskripsi kurang lengkap

## Arsitektur

```
┌─────────────────┐
│   Client        │
│  (Frontend/API) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Proposal Classification API    │
│  /api/proposal/classify/*       │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐  ┌──────────────────┐
│   PDF   │  │    Proposal      │
│ Parser  │  │   Classifier     │
│ Service │  │    Service       │
└─────────┘  └──────────────────┘
    │              │
    ▼              ▼
┌─────────┐  ┌──────────────────┐
│  PDF    │  │  IndoBERT Model  │
│  Text   │  │   (Fine-tuned)   │
└─────────┘  └──────────────────┘
```

## Komponen

### 1. PDF Parser Service (`pdf_parser_service.py`)

Service untuk parsing PDF proposal dari URL atau file lokal.

**Features:**

- Download PDF dari URL
- Extract text dari PDF menggunakan `pdfplumber` atau `pypdf`
- **Section-based extraction** menggunakan regex pattern
- Hanya mengekstrak 8 section spesifik proposal:
  - 1.1 Latar Belakang Usaha
  - 2.1 Noble Purpose
  - 2.2 Identifikasi Konsumen
  - 2.3 Produk Inovatif
  - 2.4 Strategi Pemasaran
  - 2.5 Sumber Daya
  - 3.1 Laporan/Proyeksi Keuangan
  - 3.2 Rencana Anggaran Belanja
- Error handling untuk PDF corrupt atau tidak valid

**Classes:**

- `ProposalParser`: Parser untuk extract sections dengan regex
- `PDFParserService`: Service utama untuk download dan parse PDF

**Methods:**

```python
# Extract semua teks (raw)
async def parse_pdf_from_url(pdf_url: str, extract_sections: bool = False) -> Optional[str]

# Extract sections terstruktur
async def parse_pdf_sections_from_url(pdf_url: str) -> Optional[Dict[str, str]]

# Dari file lokal
def parse_pdf_from_file(pdf_path: str, extract_sections: bool = False) -> Optional[str]
def parse_pdf_sections_from_file(pdf_path: str) -> Optional[Dict[str, str]]
```

**Section Mapping:**

```python
{
    r"1\.1\s+Latar\s+Belakang\s+Usaha": "txt_latar_belakang",
    r"2\.1\s+Noble\s+Purpose": "txt_noble_purpose",
    r"2\.2\s+Identifikasi\s+Konsumen": "txt_konsumen",
    r"2\.3\s+Produk\s+Inovatif": "txt_produk_inovatif",
    r"2\.4\s+Strategi\s+Pemasaran": "txt_strategi_pemasaran",
    r"2\.5\s+Sumber\s+Daya": "txt_sumber_daya",
    r"3\.1\s+Laporan/Proyeksi\s+Keuangan": "txt_keuangan_narrative",
    r"3\.2\s+Rencana\s+Anggaran\s+Belanja": "txt_rab_narrative",
}
```

- Extract text dari PDF menggunakan `pdfplumber` atau `pypdf`
- Error handling untuk PDF corrupt atau tidak valid

**Methods:**

```python
async def parse_pdf_from_url(pdf_url: str) -> Optional[str]
def parse_pdf_from_file(pdf_path: str) -> Optional[str]
```

### 2. Proposal Classifier Service (`proposal_classifier_service.py`)

Service untuk load model IndoBERT dan melakukan klasifikasi.

**Features:**

- Lazy loading model (singleton pattern)
- GPU support (jika tersedia)
- Confidence score untuk setiap prediksi
- Klasifikasi dari text utuh atau sections terpisah

**Methods:**

```python
def classify_proposal(proposal_text: str) -> Dict[str, Any]
def classify_proposal_sections(**kwargs) -> Dict[str, Any]
def reload_model() -> None
```

### 3. API Routes (`proposal_route.py`)

Empat endpoint untuk klasifikasi proposal:

#### POST `/api/proposal/classify/tenant/{tenant_id}`

**[RECOMMENDED]** Klasifikasi proposal berdasarkan tenant_id. Endpoint ini otomatis mengambil proposal_url dari database.

**Path Parameter:**

- `tenant_id`: ID tenant (contoh: "A1B2")

**Request:** Tidak perlu body, hanya kirim tenant_id di path

**Response:**

```json
{
  "status": "success",
  "message": "Proposal berhasil diklasifikasi",
  "data": {
    "tenant_id": "A1B2",
    "nama_bisnis": "Bisnis ABC",
    "nama_ketua_tim": "John Doe",
    "proposal_url": "https://storage.example.com/proposals/proposal_001.pdf",
    "classification": {
      "prediction": "pass",
      "confidence": 0.9543,
      "label": 1,
      "message": "PASS - Proposal memenuhi kriteria administrasi dan substansi",
      "proposal_text_length": 1250
    }
  }
}
```

**Keuntungan:**

- Tidak perlu manual input URL
- Otomatis ambil dari database
- Validasi tenant existence
- Return info tenant lengkap

#### POST `/api/proposal/classify/url`

Klasifikasi dari URL PDF.

**Request:**

```json
{
  "proposal_url": "https://storage.example.com/proposals/proposal_001.pdf"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Proposal berhasil diklasifikasi",
  "data": {
    "prediction": "pass",
    "confidence": 0.9543,
    "label": 1,
    "message": "PASS - Proposal memenuhi kriteria administrasi dan substansi",
    "proposal_text_length": 1250
  }
}
```

#### POST `/api/proposal/classify/text`

Klasifikasi dari text langsung.

**Request:**

```json
{
  "proposal_text": "Teks proposal lengkap yang akan diklasifikasi..."
}
```

#### POST `/api/proposal/classify/sections`

Klasifikasi dari sections terpisah.

**Request:**

```json
{
  "latar_belakang": "Teks latar belakang...",
  "noble_purpose": "Teks noble purpose...",
  "konsumen": "Teks konsumen...",
  "produk_inovatif": "Teks produk inovatif...",
  "strategi_pemasaran": "Teks strategi pemasaran...",
  "sumber_daya": "Teks sumber daya...",
  "keuangan_narrative": "Teks keuangan...",
  "rab_narrative": "Teks RAB..."
}
```

## Model Information

**Model:** IndoBERT Base P2 (indobenchmark/indobert-base-p2)  
**Fine-tuned on:** Dataset proposal bisnis dengan label Accepted/Rejected  
**Location:** `app/ml/indobert_full_proposal_finetuned/`  
**Input:** Teks proposal (max 512 tokens)  
**Output:** Binary classification (0 = Reject, 1 = Pass)

## Installation

### 1. Install Dependencies

```bash
# Install PDF parsing libraries
uv add pypdf pdfplumber

# Or using pip
pip install pypdf pdfplumber
```

### 2. Ensure Model Exists

Model harus ada di `app/ml/indobert_full_proposal_finetuned/`. Jika belum ada, jalankan notebook `4_Finetuning.ipynb` untuk training model.

### 3. Update Environment

Model akan di-load dari path yang ditentukan di `settings.base_dir`.

## Usage

### From Frontend/Client

```javascript
// [RECOMMENDED] Klasifikasi berdasarkan tenant_id
const response = await fetch(`/api/proposal/classify/tenant/${tenantId}`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${firebaseToken}`,
  },
});

const result = await response.json();
console.log(result.data.classification.prediction); // "pass" or "reject"
console.log(result.data.classification.confidence); // 0.9543
console.log(result.data.tenant_id); // "A1B2"
console.log(result.data.nama_bisnis); // "Bisnis ABC"

// Atau klasifikasi dari URL manual
const response2 = await fetch("/api/proposal/classify/url", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${firebaseToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    proposal_url: "https://example.com/proposal.pdf",
  }),
});

const result2 = await response2.json();
console.log(result2.data.prediction); // "pass" or "reject"
console.log(result2.data.confidence); // 0.9543
```

### From Python

```python
from app.services.proposal_classifier_service import get_proposal_classifier

# Get classifier instance
classifier = get_proposal_classifier()

# Classify text
result = classifier.classify_proposal("Teks proposal lengkap...")
print(result["prediction"])  # "pass" or "reject"
print(result["confidence"])  # 0.9543

# Classify from sections
result = classifier.classify_proposal_sections(
    latar_belakang="...",
    noble_purpose="...",
    # ... other sections
)
```

## Performance Considerations

### Model Loading

- Model di-load sekali saat aplikasi start (singleton pattern)
- Model size: ~500MB
- Load time: ~3-5 detik (CPU), ~1-2 detik (GPU)

### Inference Time

- CPU: ~200-500ms per proposal
- GPU: ~50-100ms per proposal

### Memory Usage

- Model in memory: ~500MB
- Peak memory during inference: ~1GB (dengan batch)

### Optimization Tips

1. **Use GPU if available:**

   ```python
   # Model automatically uses GPU if torch.cuda.is_available()
   ```

2. **Reuse classifier instance:**

   ```python
   # Good - reuse instance
   classifier = get_proposal_classifier()
   for proposal in proposals:
       result = classifier.classify_proposal(proposal)

   # Bad - creates new instance every time
   for proposal in proposals:
       classifier = ProposalClassifierService()  # Don't do this!
   ```

3. **Pre-process PDF text:**
   - Remove excessive whitespace
   - Normalize text encoding
   - Limit text length to 512 tokens

## Error Handling

Service menangani berbagai error scenarios:

### PDF Parsing Errors

```python
{
  "status": "error",
  "message": "Gagal mengekstrak teks dari PDF. Pastikan URL valid dan file dapat diakses.",
  "data": None
}
```

### Empty/Invalid Proposal

```python
{
  "status": "success",
  "message": "Proposal berhasil diklasifikasi",
  "data": {
    "prediction": "reject",
    "confidence": 1.0,
    "label": 0,
    "message": "Proposal kosong atau tidak valid"
  }
}
```

### Model Loading Errors

```python
# Raises FileNotFoundError if model not found
FileNotFoundError: Model tidak ditemukan di app/ml/indobert_full_proposal_finetuned/
```

## Testing

### Manual Testing

```bash
# Test classify from URL
curl -X POST "http://localhost:8000/api/proposal/classify/url" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proposal_url": "https://example.com/proposal.pdf"}'

# Test classify from text
curl -X POST "http://localhost:8000/api/proposal/classify/text" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proposal_text": "Teks proposal lengkap..."}'
```

### Automated Testing

```python
import pytest
from app.services.proposal_classifier_service import get_proposal_classifier

def test_classify_valid_proposal():
    classifier = get_proposal_classifier()
    result = classifier.classify_proposal("Teks proposal yang valid dan lengkap...")

    assert result["prediction"] in ["pass", "reject"]
    assert 0 <= result["confidence"] <= 1
    assert result["label"] in [0, 1]

def test_classify_empty_proposal():
    classifier = get_proposal_classifier()
    result = classifier.classify_proposal("")

    assert result["prediction"] == "reject"
    assert result["message"] == "Proposal kosong atau tidak valid"
```

## Troubleshooting

### Model Not Loading

**Problem:** `FileNotFoundError: Model tidak ditemukan`

**Solution:**

1. Pastikan model ada di `app/ml/indobert_full_proposal_finetuned/`
2. Jalankan notebook `4_Finetuning.ipynb` untuk training model
3. Periksa path di `settings.base_dir`

### Out of Memory

**Problem:** CUDA out of memory atau system memory full

**Solution:**

1. Reduce batch size (jika batch processing)
2. Use CPU instead of GPU
3. Increase system memory
4. Process proposals one at a time

### Slow Inference

**Problem:** Inference terlalu lambat

**Solution:**

1. Use GPU if available
2. Reduce max_length parameter (default 512)
3. Pre-process and cache PDF text
4. Consider model quantization

### PDF Parsing Fails

**Problem:** `pdfplumber` atau `pypdf` error

**Solution:**

1. Install dependencies: `uv add pypdf pdfplumber`
2. Check PDF file is not corrupted
3. Ensure PDF is readable (not image-based)
4. Try alternative PDF parser

## Future Improvements

- [ ] Batch processing untuk multiple proposals
- [ ] Model caching dengan Redis
- [ ] Async model inference
- [ ] Model quantization untuk faster inference
- [ ] Support untuk format lain (DOCX, TXT)
- [ ] Detailed feedback per section
- [ ] Multi-language support
- [ ] Model versioning

## References

- Notebook: `app/ml/4_Finetuning.ipynb`
- Model: IndoBERT Base P2 ([indobenchmark/indobert-base-p2](https://huggingface.co/indobenchmark/indobert-base-p2))
- Transformers: [Hugging Face Transformers](https://huggingface.co/docs/transformers)
