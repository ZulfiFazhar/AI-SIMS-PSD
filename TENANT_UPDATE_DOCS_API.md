# API Tenant Update dengan Replace File

## Endpoint

```
PUT /api/tenant/{tenant_id}
```

## Fitur Utama

✅ Update data form tenant  
✅ Update/replace dokumen tenant  
✅ **File lama otomatis dihapus sebelum upload file baru**  
✅ Partial update (kirim hanya field yang ingin diubah)  
✅ Ownership & status validation

## Proses Update File

1. **Delete old file** - File lama dihapus dari Cloudflare R2
2. **Upload new file** - File baru diupload
3. **Update database** - URL baru disimpan di database

## Request Headers

```
Authorization: Bearer <firebase_id_token>
Content-Type: multipart/form-data
```

## Form Fields (Semua Opsional)

### Data Tim

- `nama_ketua_tim` - string
- `nim_nidn_ketua` - string
- `nama_anggota_tim` - string (optional)
- `nim_nidn_anggota` - string (optional)
- `nomor_telepon` - string

### Data Akademik

- `fakultas` - string
- `prodi` - string

### Data Bisnis

- `nama_bisnis` - string
- `kategori_bisnis` - string
- `alamat_usaha` - string
- `jenis_usaha` - string
- `lama_usaha` - integer (dalam bulan)
- `omzet` - float

### File Uploads (Opsional - akan replace file lama)

- `logo` - file (JPG/PNG, max 2MB)
- `sertifikat_nib` - file (PDF/JPG/PNG, max 5MB)
- `proposal` - file (PDF/DOC/DOCX, max 10MB)
- `bmc` - file (PDF/JPG/PNG, max 5MB)
- `rab` - file (PDF/XLS/XLSX, max 5MB)
- `laporan_keuangan` - file (PDF/XLS/XLSX, max 10MB)
- `foto_produk[]` - multiple files (JPG/PNG, max 5MB each)
- `akun_medsos` - string (JSON format)

## Example Requests

### 1. Update Hanya Data Form

```bash
curl -X PUT "http://localhost:8000/api/tenant/TN01" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "nama_ketua_tim=John Doe Updated" \
  -F "nomor_telepon=081234567890" \
  -F "omzet=75000000"
```

### 2. Update Hanya File Proposal

```bash
curl -X PUT "http://localhost:8000/api/tenant/TN01" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "proposal=@/path/to/new-proposal.pdf"
```

**Proses:**

- File `proposal_old.pdf` dihapus dari R2
- File `new-proposal.pdf` diupload
- Database diupdate dengan URL baru

### 3. Update Data + File

```bash
curl -X PUT "http://localhost:8000/api/tenant/TN01" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "nama_bisnis=Warung Kopi Startup 2.0" \
  -F "omzet=100000000" \
  -F "logo=@/path/to/new-logo.png" \
  -F "proposal=@/path/to/new-proposal.pdf"
```

**Proses:**

1. Update data form (nama_bisnis, omzet)
2. Delete file logo lama dari R2
3. Upload logo baru
4. Delete file proposal lama dari R2
5. Upload proposal baru
6. Update database

### 4. Update Multiple Product Photos

```bash
curl -X PUT "http://localhost:8000/api/tenant/TN01" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "foto_produk=@/path/to/product1.jpg" \
  -F "foto_produk=@/path/to/product2.jpg" \
  -F "foto_produk=@/path/to/product3.jpg"
```

**Proses:**

- Semua foto produk lama dihapus dari R2
- 3 foto baru diupload
- URLs disimpan sebagai JSON array

## Success Response

```json
{
  "status": "success",
  "message": "Dokumen tenant berhasil diperbarui. 3 file lama dihapus.",
  "data": {
    "id": "TN01",
    "user_id": "A1B2",
    "nama_ketua_tim": "John Doe Updated",
    "nama_bisnis": "Warung Kopi Startup 2.0",
    "omzet": 100000000,
    "status": "pending",
    "business_documents": {
      "logo_url": "https://pub-xxx.r2.dev/tenants/TN01/logos/new-logo.png",
      "proposal_url": "https://pub-xxx.r2.dev/tenants/TN01/proposals/new-proposal.pdf",
      "foto_produk_urls": "[\"url1\", \"url2\", \"url3\"]",
      ...
    },
    ...
  }
}
```

## Error Responses

### 1. Not Owner

```json
{
  "status": "error",
  "message": "Anda tidak memiliki akses untuk mengubah dokumen tenant ini",
  "data": null
}
```

### 2. Status Not Pending

```json
{
  "status": "error",
  "message": "Dokumen tenant dengan status approved tidak dapat diubah. Hanya tenant dengan status pending yang dapat diubah.",
  "data": null
}
```

### 3. No Updates Provided

```json
{
  "status": "error",
  "message": "Tidak ada data atau file yang diupdate",
  "data": null
}
```

### 4. File Too Large

```json
{
  "status": "error",
  "message": "Gagal memperbarui dokumen tenant: Ukuran file 12.5MB melebihi batas maksimal 10MB",
  "data": null
}
```

### 5. Invalid File Type

```json
{
  "status": "error",
  "message": "Gagal memperbarui dokumen tenant: File extension .txt tidak diizinkan. Hanya .pdf, .doc, .docx yang diperbolehkan.",
  "data": null
}
```

## Validation Rules

### Ownership

- Hanya owner tenant yang bisa update
- Checked via `user_id` dari Firebase token

### Status Check

- Hanya tenant dengan status `PENDING` yang bisa diupdate
- Status `APPROVED` atau `REJECTED` tidak bisa diubah

### File Size Limits

| File Type          | Max Size |
| ------------------ | -------- |
| Logo               | 2 MB     |
| Sertifikat NIB     | 5 MB     |
| Proposal           | 10 MB    |
| BMC                | 5 MB     |
| RAB                | 5 MB     |
| Laporan Keuangan   | 10 MB    |
| Foto Produk (each) | 5 MB     |

### File Extensions

| File Type        | Allowed Extensions      |
| ---------------- | ----------------------- |
| Logo             | .jpg, .jpeg, .png       |
| Sertifikat NIB   | .pdf, .jpg, .jpeg, .png |
| Proposal         | .pdf, .doc, .docx       |
| BMC              | .pdf, .jpg, .jpeg, .png |
| RAB              | .pdf, .xls, .xlsx       |
| Laporan Keuangan | .pdf, .xls, .xlsx       |
| Foto Produk      | .jpg, .jpeg, .png       |

## Testing Scenarios

### Test 1: Update Only Form Data

```python
import requests

response = requests.put(
    "http://localhost:8000/api/tenant/TN01",
    headers={"Authorization": f"Bearer {token}"},
    data={
        "nama_ketua_tim": "John Updated",
        "omzet": 75000000
    }
)
```

### Test 2: Replace Proposal File

```python
import requests

with open("new-proposal.pdf", "rb") as f:
    response = requests.put(
        "http://localhost:8000/api/tenant/TN01",
        headers={"Authorization": f"Bearer {token}"},
        files={"proposal": f}
    )
```

### Test 3: Update Everything

```python
import requests

data = {
    "nama_ketua_tim": "John Updated",
    "omzet": 100000000,
    "akun_medsos": '{"instagram": "@updated"}'
}

files = {
    "logo": open("new-logo.png", "rb"),
    "proposal": open("new-proposal.pdf", "rb"),
    "foto_produk": [
        open("product1.jpg", "rb"),
        open("product2.jpg", "rb")
    ]
}

response = requests.put(
    "http://localhost:8000/api/tenant/TN01",
    headers={"Authorization": f"Bearer {token}"},
    data=data,
    files=files
)
```

## Implementation Details

### File Delete Logic (FileUploadService)

```python
def delete_file(self, file_url: str) -> bool:
    """
    Delete file from R2 storage.
    Returns True if successful, False otherwise.
    """
    # Extract object key from full URL
    # Delete from R2 using boto3
    # Returns boolean status
```

### Update Documents Logic (TenantService)

```python
async def update_tenant_documents(...):
    # 1. Validate ownership & status
    # 2. Get existing documents
    # 3. For each new file:
    #    - Add old file URL to delete list
    #    - Upload new file
    #    - Store new URL
    # 4. Update database
    # 5. Delete old files from R2
    # 6. Return result with delete count
```

## Benefits

✅ **Automatic cleanup** - No orphaned files in storage  
✅ **Storage optimization** - Old files removed immediately  
✅ **Flexible updates** - Update any combination of fields/files  
✅ **Secure** - Ownership & status validation  
✅ **Logging** - Track all file operations  
✅ **Error handling** - Rollback on failures

## Notes

1. **Delete happens AFTER database commit** - Ensures data consistency
2. **Delete failures are logged** - Won't block the update
3. **Partial updates supported** - Send only changed fields
4. **Multiple file arrays handled** - foto_produk can have multiple files
5. **Status check critical** - Only PENDING tenants can update
