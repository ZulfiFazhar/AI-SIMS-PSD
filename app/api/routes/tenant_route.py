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


router = APIRouter(prefix="/tenant", tags=["Tenant"])


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    """Dependency to get TenantService with repositories"""
    tenant_repo = TenantRepository(db)
    doc_repo = BusinessDocumentRepository(db)
    return TenantService(tenant_repo, doc_repo)


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


@router.put("/{tenant_id}/status", response_model=BaseResponse)
async def update_tenant_status(
    tenant_id: str,
    request: TenantUpdateStatusRequest,
    tenant_service: TenantService = Depends(get_tenant_service),
    user_id: str = Depends(get_user_id_from_firebase),
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

    **Note:** Endpoint ini harus dilindungi dengan role check (admin only).
    TODO: Tambahkan middleware untuk check admin role.
    """
    # TODO: Add admin role check middleware
    # For now, allow any authenticated user (should be restricted to admin only)

    return tenant_service.update_tenant_status(
        tenant_id=tenant_id,
        status=request.status,
        rejection_reason=request.rejection_reason,
    )


@router.post("/upload-test", response_model=BaseResponse)
async def upload_test_file(
    file: UploadFile = File(...),
):
    """
    Test endpoint untuk upload single file dokumen bisnis.
    
    **File upload:**
    - file (JPG/PNG/PDF/DOC/DOCX/XLS/XLSX, max 10MB)
    
    **Example using curl:**
    ```bash
    curl -X POST http://localhost:8000/api/tenant/upload-test \
      -F "file=@document.pdf"
    ```
    """
    from app.services.file_upload_service import file_upload_service
    from app.core.schema import create_success_response, create_error_response

    try:
        url = await file_upload_service.upload_file(
            file,
            folder="test-uploads",
            allowed_extensions=[
                ".jpg",
                ".jpeg",
                ".png",
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
            ],
            max_size_mb=10,
        )

        return create_success_response(
            message="File uploaded successfully",
            data={"file_url": url, "filename": file.filename},
        )
    except Exception as e:
        return create_error_response(message=f"Upload failed: {str(e)}")


@router.post("/upload-multiple-test", response_model=BaseResponse)
async def upload_multiple_test_files(
    # Form fields (wajib)
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
    # Form fields (opsional)
    nama_anggota_tim: Optional[str] = Form(None),
    nim_nidn_anggota: Optional[str] = Form(None),
    akun_medsos: Optional[str] = Form(None),
    # File uploads (semua opsional)
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
    Test endpoint untuk upload complete tenant registration (form + files).

    **Proses bisnis:**
    1. Pengguna mengisi formulir pendaftaran tenant
    2. Pengguna mengupload dokumen bisnis yang diperlukan
    3. Sistem menyimpan data dan mengatur status menjadi 'pending'

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

    """
    try:
        # Prepare form data response
        form_data = {
            "user_id": user_id,
            "nama_ketua_tim": nama_ketua_tim,
            "nim_nidn_ketua": nim_nidn_ketua,
            "nomor_telepon": nomor_telepon,
            "fakultas": fakultas,
            "prodi": prodi,
            "nama_bisnis": nama_bisnis,
            "kategori_bisnis": kategori_bisnis,
            "alamat_usaha": alamat_usaha,
            "jenis_usaha": jenis_usaha,
            "lama_usaha": lama_usaha,
            "omzet": omzet,
            "nama_anggota_tim": nama_anggota_tim,
            "nim_nidn_anggota": nim_nidn_anggota,
            "akun_medsos": akun_medsos,
        }

        uploaded_files = {}

        # Upload logo
        if logo and logo.filename:
            url = await file_upload_service.upload_file(
                logo,
                folder="test-uploads/logos",
                allowed_extensions=[".jpg", ".jpeg", ".png"],
                max_size_mb=2,
            )
            uploaded_files["logo"] = url

        # Upload sertifikat NIB
        if sertifikat_nib and sertifikat_nib.filename:
            url = await file_upload_service.upload_file(
                sertifikat_nib,
                folder="test-uploads/documents",
                allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                max_size_mb=5,
            )
            uploaded_files["sertifikat_nib"] = url

        # Upload proposal
        if proposal and proposal.filename:
            url = await file_upload_service.upload_file(
                proposal,
                folder="test-uploads/documents",
                allowed_extensions=[".pdf", ".doc", ".docx"],
                max_size_mb=10,
            )
            uploaded_files["proposal"] = url

        # Upload BMC
        if bmc and bmc.filename:
            url = await file_upload_service.upload_file(
                bmc,
                folder="test-uploads/documents",
                allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                max_size_mb=5,
            )
            uploaded_files["bmc"] = url

        # Upload RAB
        if rab and rab.filename:
            url = await file_upload_service.upload_file(
                rab,
                folder="test-uploads/documents",
                allowed_extensions=[".pdf", ".xls", ".xlsx"],
                max_size_mb=5,
            )
            uploaded_files["rab"] = url

        # Upload laporan keuangan
        if laporan_keuangan and laporan_keuangan.filename:
            url = await file_upload_service.upload_file(
                laporan_keuangan,
                folder="test-uploads/documents",
                allowed_extensions=[".pdf", ".xls", ".xlsx"],
                max_size_mb=10,
            )
            uploaded_files["laporan_keuangan"] = url

        # Upload foto produk (multiple files)
        if foto_produk and len(foto_produk) > 0:
            foto_urls = await file_upload_service.upload_multiple_files(
                [f for f in foto_produk if f.filename],
                folder="test-uploads/products",
                allowed_extensions=[".jpg", ".jpeg", ".png"],
                max_size_mb=5,
            )
            if foto_urls:
                uploaded_files["foto_produk"] = foto_urls

        return create_success_response(
            message="Test registration data received and files uploaded successfully",
            data={
                "form_data": form_data,
                "uploaded_files": uploaded_files,
                "files_count": len(uploaded_files),
            },
        )
    except Exception as e:
        return create_error_response(message=f"Test failed: {str(e)}")
