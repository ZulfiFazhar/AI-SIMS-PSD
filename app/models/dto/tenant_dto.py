from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TenantRegisterRequest(BaseModel):
    """Request body for tenant registration (form fields only)"""

    # Team information
    nama_ketua_tim: str = Field(..., min_length=1, max_length=255)
    nim_nidn_ketua: str = Field(..., min_length=1, max_length=50)
    nama_anggota_tim: Optional[str] = Field(None, max_length=255)
    nim_nidn_anggota: Optional[str] = Field(None, max_length=50)
    nomor_telepon: str = Field(..., min_length=10, max_length=20)

    # Academic information
    fakultas: str = Field(..., min_length=1, max_length=100)
    prodi: str = Field(..., min_length=1, max_length=100)

    # Business information
    nama_bisnis: str = Field(..., min_length=1, max_length=255)
    kategori_bisnis: str = Field(..., min_length=1, max_length=100)
    alamat_usaha: str = Field(..., min_length=1)
    jenis_usaha: str = Field(..., min_length=1, max_length=100)
    lama_usaha: int = Field(..., ge=0, description="Lama usaha dalam bulan")
    omzet: Decimal = Field(..., ge=0, description="Omzet usaha")

    # Social media accounts (JSON string)
    akun_medsos: Optional[str] = Field(
        None, description="JSON string of social media accounts"
    )

    @field_validator("nomor_telepon")
    @classmethod
    def validate_phone(cls, value):
        """Validate phone number format"""
        # Remove spaces and dashes
        cleaned = value.replace(" ", "").replace("-", "")
        if not cleaned.isdigit():
            raise ValueError("Nomor telepon harus berisi angka saja")
        if not cleaned.startswith(("08", "62", "+62")):
            raise ValueError("Nomor telepon harus dimulai dengan 08, 62, atau +62")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "nama_ketua_tim": "John Doe",
                "nim_nidn_ketua": "1234567890",
                "nama_anggota_tim": "Jane Smith",
                "nim_nidn_anggota": "0987654321",
                "nomor_telepon": "081234567890",
                "fakultas": "Fakultas Teknik",
                "prodi": "Teknik Informatika",
                "nama_bisnis": "Warung Kopi Startup",
                "kategori_bisnis": "Food & Beverage",
                "alamat_usaha": "Jl. Contoh No. 123, Jakarta",
                "jenis_usaha": "Kafe",
                "lama_usaha": 12,
                "omzet": 50000000,
                "akun_medsos": '{"instagram": "@warungkopi", "tiktok": "@warungkopi"}',
            }
        }


class TenantUpdateRequest(BaseModel):
    """Request body for updating tenant data"""

    # Team information
    nama_ketua_tim: Optional[str] = Field(None, min_length=1, max_length=255)
    nim_nidn_ketua: Optional[str] = Field(None, min_length=1, max_length=50)
    nama_anggota_tim: Optional[str] = Field(None, max_length=255)
    nim_nidn_anggota: Optional[str] = Field(None, max_length=50)
    nomor_telepon: Optional[str] = Field(None, min_length=10, max_length=20)

    # Academic information
    fakultas: Optional[str] = Field(None, min_length=1, max_length=100)
    prodi: Optional[str] = Field(None, min_length=1, max_length=100)

    # Business information
    nama_bisnis: Optional[str] = Field(None, min_length=1, max_length=255)
    kategori_bisnis: Optional[str] = Field(None, min_length=1, max_length=100)
    alamat_usaha: Optional[str] = Field(None, min_length=1)
    jenis_usaha: Optional[str] = Field(None, min_length=1, max_length=100)
    lama_usaha: Optional[int] = Field(None, ge=0, description="Lama usaha dalam bulan")
    omzet: Optional[Decimal] = Field(None, ge=0, description="Omzet usaha")

    # Social media accounts (JSON string)
    akun_medsos: Optional[str] = Field(
        None, description="JSON string of social media accounts"
    )

    @field_validator("nomor_telepon")
    @classmethod
    def validate_phone(cls, value):
        """Validate phone number format"""
        if value is None:
            return value
        # Remove spaces and dashes
        cleaned = value.replace(" ", "").replace("-", "")
        if not cleaned.isdigit():
            raise ValueError("Nomor telepon harus berisi angka saja")
        if not cleaned.startswith(("08", "62", "+62")):
            raise ValueError("Nomor telepon harus dimulai dengan 08, 62, atau +62")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "nama_ketua_tim": "John Doe Updated",
                "nomor_telepon": "081234567890",
                "nama_bisnis": "Warung Kopi Startup 2.0",
                "omzet": 75000000,
            }
        }


class BusinessDocumentRequest(BaseModel):
    """
    Request body for business document uploads
    """
    id: int
    logo_url: Optional[str] = None
    akun_medsos: Optional[str] = None
    sertifikat_nib_url: Optional[str] = None
    proposal_url: Optional[str] = None
    bmc_url: Optional[str] = None
    rab_url: Optional[str] = None
    laporan_keuangan_url: Optional[str] = None
    foto_produk_urls: Optional[str] = None

class BusinessDocumentResponse(BaseModel):
    """Business document information response"""

    id: int
    tenant_id: str
    logo_url: Optional[str] = None
    akun_medsos: Optional[str] = None
    sertifikat_nib_url: Optional[str] = None
    proposal_url: Optional[str] = None
    bmc_url: Optional[str] = None
    rab_url: Optional[str] = None
    laporan_keuangan_url: Optional[str] = None
    foto_produk_urls: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantResponse(BaseModel):
    """Tenant information response"""

    id: str
    user_id: str
    nama_ketua_tim: str
    nim_nidn_ketua: str
    nama_anggota_tim: Optional[str] = None
    nim_nidn_anggota: Optional[str] = None
    nomor_telepon: str
    fakultas: str
    prodi: str
    nama_bisnis: str
    kategori_bisnis: str
    alamat_usaha: str
    jenis_usaha: str
    lama_usaha: int
    omzet: Decimal
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    business_documents: Optional[BusinessDocumentResponse] = None

    class Config:
        from_attributes = True


class TenantRegistrationResponse(BaseModel):
    """Response for tenant registration"""

    tenant: TenantResponse
    message: str = "Pendaftaran tenant berhasil dikirim. Menunggu persetujuan admin."

    class Config:
        json_schema_extra = {
            "example": {
                "tenant": {
                    "id": "TN01",
                    "user_id": "A1B2",
                    "nama_ketua_tim": "John Doe",
                    "nama_bisnis": "Warung Kopi Startup",
                    "status": "pending",
                },
                "message": "Pendaftaran tenant berhasil dikirim. Menunggu persetujuan admin.",
            }
        }


class TenantUpdateStatusRequest(BaseModel):
    """Request body for updating tenant status (admin only)"""

    status: str = Field(..., description="Status: approved or rejected")
    rejection_reason: Optional[str] = Field(
        None, description="Alasan penolakan jika status=rejected"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        """Validate status value"""
        if value not in ["approved", "rejected"]:
            raise ValueError("Status harus 'approved' atau 'rejected'")
        return value

    @field_validator("rejection_reason")
    @classmethod
    def validate_rejection_reason(cls, value, info):
        """Require rejection reason if status is rejected"""
        if info.data.get("status") == "rejected" and not value:
            raise ValueError("rejection_reason wajib diisi jika status=rejected")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "status": "approved",
                "rejection_reason": None,
            }
        }
