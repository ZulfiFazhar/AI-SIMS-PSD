# ML Model Setup

Model machine learning **TIDAK** disimpan di Git repository karena ukuran terlalu besar (>100MB).

## Download Model

### Option 1: Train Model Sendiri (Recommended untuk Development)

1. Buka notebook:

   ```bash
   jupyter notebook app/ml/4_Finetuning.ipynb
   ```

2. Jalankan semua cell untuk training model

3. Model akan otomatis tersimpan di `app/ml/indobert_full_proposal_finetuned/`

### Option 2: Download Pre-trained Model

Jika ada tim member yang sudah train model, share melalui:

**Google Drive:**

1. Upload folder `indobert_full_proposal_finetuned/` ke Google Drive
2. Share link dengan team
3. Download dan extract ke `app/ml/`

**Cloud Storage (R2/S3):**

1. Upload ke Cloudflare R2 atau AWS S3
2. Generate signed URL
3. Download via:
   ```bash
   # Example
   curl -o model.zip "SIGNED_URL"
   unzip model.zip -d app/ml/
   ```

## Verify Model Installation

```bash
# Check if model exists
ls app/ml/indobert_full_proposal_finetuned/

# Should contain:
# - config.json
# - model.safetensors (atau pytorch_model.bin)
# - tokenizer_config.json
# - vocab.txt
# - special_tokens_map.json
```

## Model Size

- **Total Size**: ~500 MB
- **Main File**: model.safetensors (474 MB)
- **Config & Tokenizer**: ~26 MB

## Troubleshooting

### Model Not Found Error

```
FileNotFoundError: Model tidak ditemukan di app/ml/indobert_full_proposal_finetuned/
```

**Solution:**

1. Ensure folder exists: `app/ml/indobert_full_proposal_finetuned/`
2. Check folder contains `model.safetensors` or `pytorch_model.bin`
3. Re-train model jika file corrupt

### Out of Disk Space

Model requires ~500 MB disk space.

**Solution:**

1. Free up disk space
2. Move model to external drive (update path di config)

## Git LFS Alternative (Optional)

Jika team ingin track model dengan Git, gunakan Git LFS:

```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "app/ml/**/*.safetensors"
git lfs track "app/ml/**/*.bin"

# Add to git
git add .gitattributes
git add app/ml/indobert_full_proposal_finetuned/
git commit -m "Add model with LFS"
git push origin dev
```

**Note:** Git LFS memerlukan storage tambahan dan mungkin ada biaya.

## Best Practices

### For Development

- Train model locally
- Share via cloud storage (bukan git)
- Document model version dan training params

### For Production

- Store model di cloud storage (R2/S3)
- Load model dari URL saat deployment
- Use model versioning

### For Team Collaboration

- One person trains → share via Google Drive
- Document training date dan accuracy
- Update notebook jika ada perubahan dataset

## Model Update Workflow

1. Update training notebook
2. Train new model
3. Test performance
4. If better → share new model
5. Update CHANGELOG with model version

## Security

⚠️ **NEVER commit model to public repository!**

Reasons:

- Too large (GitHub will reject)
- Can be regenerated from notebook
- May contain sensitive training data
- Wastes repository space

✅ **DO:**

- Add to .gitignore
- Share via private cloud storage
- Document training process
- Version control the training code

❌ **DON'T:**

- Commit model files to git
- Share model publicly (unless intended)
- Include training data in repository
