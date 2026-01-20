# Setup Instructions for Proposal Classification Service

## Dependencies Installation

Untuk menggunakan service klasifikasi proposal, install dependencies berikut:

```bash
# Install PDF parsing libraries
uv add pypdf pdfplumber

# Atau jika menggunakan pip
pip install pypdf pdfplumber
```

## Dependencies yang Sudah Terinstall

Dependencies berikut sudah ada di `pyproject.toml`:

- `transformers[torch]>=4.57.3` - untuk load model BERT
- `torch>=2.9.1` - PyTorch untuk inference
- `numpy>=2.2.6` - untuk operasi array
- `scikit-learn>=1.7.2` - untuk metrics (jika diperlukan)

## Verify Installation

```bash
# Check if dependencies installed
uv pip list | grep -E "pypdf|pdfplumber|transformers|torch"
```

## Model Setup

Model sudah ada di `app/ml/indobert_full_proposal_finetuned/`. Jika belum ada:

1. Buka notebook `app/ml/4_Finetuning.ipynb`
2. Jalankan semua cell untuk training model
3. Model akan disimpan di `./indobert_full_proposal_finetuned`
4. Pastikan folder tersebut ada di `app/ml/`

## Test Service

```bash
# Start server
uv run fastapi dev

# Test endpoint - Klasifikasi berdasarkan tenant_id (RECOMMENDED)
curl -X POST http://localhost:8000/api/proposal/classify/tenant/A1B2 \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"

# Test endpoint - Klasifikasi dari text
curl -X POST http://localhost:8000/api/proposal/classify/text \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proposal_text": "Tujuan mulia kami adalah memulihkan ekosistem tanah di wilayah Jawa Barat yang mulai kritis akibat residu kimia. Kami ingin memberikan dampak positif berupa peningkatan kesehatan lahan jangka panjang serta membantu petani lokal meningkatkan pendapatan mereka melalui hasil panen yang lebih organik dan berkelanjutan, sehingga generasi mendatang masih dapat menikmati hasil bumi yang sehat."}'

# Test endpoint - Klasifikasi dari URL
curl -X POST http://localhost:8000/api/proposal/classify/url \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proposal_url": "https://example.com/proposal.pdf"}'
```

## Expected Responses

### Response dari endpoint tenant (RECOMMENDED)

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
      "confidence": 0.95,
      "label": 1,
      "message": "PASS - Proposal memenuhi kriteria administrasi dan substansi",
      "proposal_text_length": 1250
    }
  }
}
```

### Response dari endpoint text/url

```json
{
  "status": "success",
  "message": "Proposal berhasil diklasifikasi",
  "data": {
    "prediction": "pass",
    "confidence": 0.95,
    "label": 1,
    "message": "PASS - Proposal memenuhi kriteria administrasi dan substansi",
    "proposal_text_length": 400
  }
}
```
