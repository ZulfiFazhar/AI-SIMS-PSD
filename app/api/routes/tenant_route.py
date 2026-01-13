"""
Tenant routes for tenant registration and management.
"""

from fastapi import APIRouter, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.middleware import get_current_user_firebase_uid
from app.core.schema import BaseResponse, create_success_response, create_error_response
from app.models.dto.tenant_dto import TenantRegisterRequest, TenantUpdateStatusRequest
from app.services.file_upload_service import file_upload_service
from app.services.tenant_service import TenantService
from app.repositories.tenant_repository import (
    TenantRepository,
    BusinessDocumentRepository,
)
from app.repositories.user_repository import UserRepository
from app.models.user_model import UserRole


router = APIRouter(prefix="/tenant", tags=["Tenant"])


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    """Dependency to get TenantService with repositories"""
    tenant_repo = TenantRepository(db)
    doc_repo = BusinessDocumentRepository(db)
    user_repo = UserRepository(db)
    return TenantService(tenant_repo, doc_repo, user_repo)


def get_user_id_from_firebase(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db),
) -> str:
    """Get user ID from Firebase UID"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_firebase_uid(firebase_uid)
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user.id


def require_admin_role(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db),
) -> str:
    """Dependency untuk memastikan user adalah admin"""
    from fastapi import HTTPException
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_firebase_uid(firebase_uid)
    
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Akses ditolak. Hanya admin yang dapat mengakses endpoint ini."
        )
    
    return user.id


@router.post("/register", response_model=BaseResponse)
async def register_tenant(
    # Form fields
    nama_ketua_tim: str = Form(...),
    nim_nidn_ketua: str = Form(...),
    nomor_telepon: str = Form(...),
    fakultas: str = Form(...),
    prodi: str = Form(...),
    nama_bisnis: str = Form(...),
    kategori_bisnis: str = Form(...),
    alamat_usaha: str = Form(...),
    jenis_usaha: str = Form(...),
    lama_usaha: int = Form(...),
    omzet: float = Form(...),
    nama_anggota_tim: Optional[str] = Form(None),
    nim_nidn_anggota: Optional[str] = Form(None),
    akun_medsos: Optional[str] = Form(None),
    # File uploads
    logo: Optional[UploadFile] = File(None),
    sertifikat_nib: Optional[UploadFile] = File(None),
    proposal: Optional[UploadFile] = File(None),
    bmc: Optional[UploadFile] = File(None),
    rab: Optional[UploadFile] = File(None),
    laporan_keuangan: Optional[UploadFile] = File(None),
    foto_produk: Optional[List[UploadFile]] = File(None),
    # Dependencies
    user_id: str = Depends(get_user_id_from_firebase),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """
    Daftar sebagai tenant dengan upload dokumen.

    **Proses bisnis:**
    1. Pengguna mengisi formulir pendaftaran tenant
    2. Pengguna mengupload dokumen bisnis yang diperlukan
    3. Sistem menyimpan data dan mengatur status menjadi 'pending'
    4. Admin akan mereview dan menyetujui/menolak pendaftaran

    **Form fields yang wajib diisi:**
    - nama_ketua_tim
    - nim_nidn_ketua
    - nomor_telepon
    - fakultas
    - prodi
    - nama_bisnis
    - kategori_bisnis
    - alamat_usaha
    - jenis_usaha
    - lama_usaha (dalam bulan)
    - omzet

    **Form fields opsional:**
    - nama_anggota_tim
    - nim_nidn_anggota
    - akun_medsos (JSON string, contoh: '{"instagram": "@bisnisku", "tiktok": "@bisnisku"}')

    **File uploads (semua opsional):**
    - logo (JPG/PNG, max 2MB)
    - sertifikat_nib (PDF/JPG/PNG, max 5MB)
    - proposal (PDF/DOC/DOCX, max 10MB)
    - bmc (PDF/JPG/PNG, max 5MB)
    - rab (PDF/XLS/XLSX, max 5MB)
    - laporan_keuangan (PDF/XLS/XLSX, max 10MB)
    - foto_produk[] (Multiple JPG/PNG, max 5MB per file)

    **Requires authentication:**
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    # Create DTO from form data
    data = TenantRegisterRequest(
        nama_ketua_tim=nama_ketua_tim,
        nim_nidn_ketua=nim_nidn_ketua,
        nama_anggota_tim=nama_anggota_tim,
        nim_nidn_anggota=nim_nidn_anggota,
        nomor_telepon=nomor_telepon,
        fakultas=fakultas,
        prodi=prodi,
        nama_bisnis=nama_bisnis,
        kategori_bisnis=kategori_bisnis,
        alamat_usaha=alamat_usaha,
        jenis_usaha=jenis_usaha,
        lama_usaha=lama_usaha,
        omzet=omzet,
        akun_medsos=akun_medsos,
    )

    return await tenant_service.register_tenant(
        user_id=user_id,
        data=data,
        logo=logo,
        sertifikat_nib=sertifikat_nib,
        proposal=proposal,
        bmc=bmc,
        rab=rab,
        laporan_keuangan=laporan_keuangan,
        foto_produk=foto_produk,
    )


@router.get("/me", response_model=BaseResponse)
async def get_my_tenant_registration(
    user_id: str = Depends(get_user_id_from_firebase),
    tenant_service: TenantService = Depends(get_tenant_service),
):
    """
    Lihat status pendaftaran tenant saya.

    **Returns:**
    - Data tenant beserta dokumen bisnis
    - Status pendaftaran (pending/approved/rejected)
    - Alasan penolakan (jika ditolak)

    **Requires authentication:**
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    return tenant_service.get_tenant_by_user_id(user_id)


@router.get("/", response_model=BaseResponse)
async def get_all_tenants(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    tenant_service: TenantService = Depends(get_tenant_service),
    admin_id: str = Depends(require_admin_role),
):
    """
    Dapatkan semua tenant (Admin only).

    **Query Parameters:**
    - status (optional): Filter berdasarkan status (pending/approved/rejected)
    - skip (optional): Jumlah record yang dilewati untuk pagination (default: 0)
    - limit (optional): Jumlah maksimal record yang dikembalikan (default: 100, max: 100)

    **Returns:**
    - List semua tenant beserta dokumen bisnis
    - Total tenant yang dikembalikan
    - Informasi pagination

    **Requires authentication:**
    ```
    Authorization: Bearer <firebase_id_token>
    ```

    **Note:** Endpoint ini dilindungi dengan role check admin.
    Hanya user dengan role ADMIN yang dapat mengakses endpoint ini.
    """
    from app.models.tenant_model import TenantStatus
    
    # Convert string status to enum if provided
    status_enum = None
    if status:
        try:
            status_enum = TenantStatus(status)
        except ValueError:
            from app.core.schema import create_error_response
            return create_error_response(
                message=f"Status tidak valid. Gunakan: pending, approved, atau rejected"
            )
    
    return tenant_service.get_all_tenants(
        status=status_enum,
        skip=skip,
        limit=limit,
    )


@router.put("/{tenant_id}/status", response_model=BaseResponse)
async def update_tenant_status(
    tenant_id: str,
    request: TenantUpdateStatusRequest,
    tenant_service: TenantService = Depends(get_tenant_service),
    admin_id: str = Depends(require_admin_role),
):
    """
    Update status pendaftaran tenant (Admin only).

    **Admin dapat:**
    - Menyetujui pendaftaran (status: approved)
    - Menolak pendaftaran (status: rejected) dengan alasan penolakan

    **Body:**
    ```json
    {
        "status": "approved",  // atau "rejected"
        "rejection_reason": "Alasan penolakan (wajib jika rejected)"
    }
    ```

    **Requires authentication:**
    ```
    Authorization: Bearer <firebase_id_token>
    ```

    **Note:** Endpoint ini dilindungi dengan role check admin.
    Hanya user dengan role ADMIN yang dapat mengakses endpoint ini.
    """
    return tenant_service.update_tenant_status(
        tenant_id=tenant_id,
        status=request.status,
        rejection_reason=request.rejection_reason,
    )