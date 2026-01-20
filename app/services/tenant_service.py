import logging
import json
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.tenant_model import TenantStatus, Tenant, BusinessDocument
from app.models.user_model import UserRole
from app.models.dto.tenant_dto import TenantRegisterRequest, TenantUpdateRequest
from app.repositories.tenant_repository import (
    TenantRepository,
    BusinessDocumentRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.file_upload_service import file_upload_service
from app.core.schema import BaseResponse, create_success_response, create_error_response

logger = logging.getLogger(__name__)


class TenantService:
    """Service class for tenant business logic"""

    def __init__(
        self,
        tenant_repository: TenantRepository,
        business_document_repository: BusinessDocumentRepository,
        user_repository: UserRepository,
    ):
        self.tenant_repo = tenant_repository
        self.doc_repo = business_document_repository
        self.user_repo = user_repository

    def _get_tenant_with_documents(self, tenant: Tenant) -> Dict[str, Any]:
        """
        Get tenant data with business documents using model's to_dict() method.
        
        Args:
            tenant: Tenant model instance
            
        Returns:
            Dictionary with tenant and business documents data
        """
        tenant_dict = tenant.to_dict()
        
        # Include business documents if exists
        if tenant.business_documents and len(tenant.business_documents) > 0:
            tenant_dict["business_documents"] = tenant.business_documents[0].to_dict()
        else:
            tenant_dict["business_documents"] = None
            
        return tenant_dict

    async def _upload_tenant_files(
        self,
        tenant_id: str,
        logo: Optional[UploadFile] = None,
        sertifikat_nib: Optional[UploadFile] = None,
        proposal: Optional[UploadFile] = None,
        bmc: Optional[UploadFile] = None,
        rab: Optional[UploadFile] = None,
        laporan_keuangan: Optional[UploadFile] = None,
        foto_produk: Optional[List[UploadFile]] = None,
    ) -> Dict[str, Optional[str]]:
        """
        Upload all tenant files and return URLs.
        
        Args:
            tenant_id: Tenant ID for folder organization
            logo: Logo file
            sertifikat_nib: NIB certificate file
            proposal: Proposal file
            bmc: BMC file
            rab: RAB file
            laporan_keuangan: Financial report file
            foto_produk: List of product photo files
            
        Returns:
            Dictionary with file URLs
            
        Raises:
            Exception: If file upload fails
        """
        file_urls = {
            "logo_url": None,
            "sertifikat_nib_url": None,
            "proposal_url": None,
            "bmc_url": None,
            "rab_url": None,
            "laporan_keuangan_url": None,
            "foto_produk_urls": None,
        }

        # Upload logo
        if logo and logo.filename:
            logger.info(f"Uploading logo: {logo.filename}")
            file_urls["logo_url"] = await file_upload_service.upload_file(
                logo,
                folder=f"tenants/{tenant_id}/logos",
                allowed_extensions=[".jpg", ".jpeg", ".png"],
                max_size_mb=2,
                filename=logo.filename.rsplit('.', 1)[0],
            )
            logger.info(f"Logo uploaded: {file_urls['logo_url']}")

        # Upload sertifikat NIB
        if sertifikat_nib and sertifikat_nib.filename:
            logger.info(f"Uploading sertifikat NIB: {sertifikat_nib.filename}")
            file_urls["sertifikat_nib_url"] = await file_upload_service.upload_file(
                sertifikat_nib,
                folder=f"tenants/{tenant_id}/documents",
                allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                max_size_mb=5,
                filename=sertifikat_nib.filename.rsplit('.', 1)[0],
            )
            logger.info(f"Sertifikat NIB uploaded: {file_urls['sertifikat_nib_url']}")

        # Upload proposal
        if proposal and proposal.filename:
            logger.info(f"Uploading proposal: {proposal.filename}")
            file_urls["proposal_url"] = await file_upload_service.upload_file(
                proposal,
                folder=f"tenants/{tenant_id}/documents",
                allowed_extensions=[".pdf", ".doc", ".docx"],
                max_size_mb=10,
                filename=proposal.filename.rsplit('.', 1)[0],
            )
            logger.info(f"Proposal uploaded: {file_urls['proposal_url']}")

        # Upload BMC
        if bmc and bmc.filename:
            logger.info(f"Uploading BMC: {bmc.filename}")
            file_urls["bmc_url"] = await file_upload_service.upload_file(
                bmc,
                folder=f"tenants/{tenant_id}/documents",
                allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                max_size_mb=5,
                filename=bmc.filename.rsplit('.', 1)[0],
            )
            logger.info(f"BMC uploaded: {file_urls['bmc_url']}")

        # Upload RAB
        if rab and rab.filename:
            logger.info(f"Uploading RAB: {rab.filename}")
            file_urls["rab_url"] = await file_upload_service.upload_file(
                rab,
                folder=f"tenants/{tenant_id}/documents",
                allowed_extensions=[".pdf", ".xls", ".xlsx"],
                max_size_mb=5,
                filename=rab.filename.rsplit('.', 1)[0],
            )
            logger.info(f"RAB uploaded: {file_urls['rab_url']}")

        # Upload laporan keuangan
        if laporan_keuangan and laporan_keuangan.filename:
            logger.info(f"Uploading laporan keuangan: {laporan_keuangan.filename}")
            file_urls["laporan_keuangan_url"] = await file_upload_service.upload_file(
                laporan_keuangan,
                folder=f"tenants/{tenant_id}/documents",
                allowed_extensions=[".pdf", ".xls", ".xlsx"],
                max_size_mb=10,
                filename=laporan_keuangan.filename.rsplit('.', 1)[0],
            )
            logger.info(f"Laporan keuangan uploaded: {file_urls['laporan_keuangan_url']}")

        # Upload foto produk (multiple files)
        if foto_produk and len(foto_produk) > 0:
            logger.info(f"Uploading {len(foto_produk)} foto produk")
            foto_urls = await file_upload_service.upload_multiple_files(
                [f for f in foto_produk if f.filename],
                folder=f"tenants/{tenant_id}/products",
                allowed_extensions=[".jpg", ".jpeg", ".png"],
                max_size_mb=5,
                filename=foto_produk[0].filename.rsplit('.', 1)[0] if foto_produk else None,
            )
            if foto_urls:
                file_urls["foto_produk_urls"] = json.dumps(foto_urls)
                logger.info(f"Foto produk uploaded: {len(foto_urls)} files")

        return file_urls

    async def register_tenant(
        self,
        user_id: str,
        data: TenantRegisterRequest,
        logo: Optional[UploadFile] = None,
        sertifikat_nib: Optional[UploadFile] = None,
        proposal: Optional[UploadFile] = None,
        bmc: Optional[UploadFile] = None,
        rab: Optional[UploadFile] = None,
        laporan_keuangan: Optional[UploadFile] = None,
        foto_produk: Optional[List[UploadFile]] = None,
    ) -> BaseResponse:
        """
        Register new tenant with file uploads.

        Args:
            user_id: User ID from authentication
            data: Tenant registration data (TenantRegisterRequest)
            logo: Logo file
            sertifikat_nib: NIB certificate file
            proposal: Proposal file
            bmc: BMC file
            rab: RAB file
            laporan_keuangan: Financial report file
            foto_produk: List of product photo files

        Returns:
            BaseResponse with tenant data
        """
        try:
            # Check if user already registered as tenant
            existing_tenant = self.tenant_repo.get_by_user_id(user_id)
            if existing_tenant:
                return create_error_response(
                    message="Anda sudah terdaftar sebagai tenant. "
                    f"Status pendaftaran: {existing_tenant.status.value}"
                )

            # Create tenant record
            tenant = self.tenant_repo.create(
                user_id=user_id,
                nama_ketua_tim=data.nama_ketua_tim,
                nim_nidn_ketua=data.nim_nidn_ketua,
                nama_anggota_tim=data.nama_anggota_tim,
                nim_nidn_anggota=data.nim_nidn_anggota,
                nomor_telepon=data.nomor_telepon,
                fakultas=data.fakultas,
                prodi=data.prodi,
                nama_bisnis=data.nama_bisnis,
                kategori_bisnis=data.kategori_bisnis,
                alamat_usaha=data.alamat_usaha,
                jenis_usaha=data.jenis_usaha,
                lama_usaha=data.lama_usaha,
                omzet=float(data.omzet),
            )

            # Commit tenant first to get tenant_id
            self.tenant_repo.commit()
            self.tenant_repo.refresh(tenant)

            logger.info(f"Tenant created: {tenant.id} for user {user_id}")

            # Upload files
            try:
                file_urls = await self._upload_tenant_files(
                    tenant_id=tenant.id,
                    logo=logo,
                    sertifikat_nib=sertifikat_nib,
                    proposal=proposal,
                    bmc=bmc,
                    rab=rab,
                    laporan_keuangan=laporan_keuangan,
                    foto_produk=foto_produk,
                )
            except Exception as upload_error:
                logger.error(
                    f"File upload error: {type(upload_error).__name__} - {str(upload_error)}",
                    exc_info=True,
                )
                # Rollback tenant creation if file upload fails
                self.tenant_repo.rollback()
                return create_error_response(
                    message=f"Gagal mengupload file: {str(upload_error)}"
                )

            # Create business documents record with uploaded URLs
            business_doc = self.doc_repo.create(
                tenant_id=tenant.id,
                logo_url=file_urls["logo_url"],
                akun_medsos=data.akun_medsos,
                sertifikat_nib_url=file_urls["sertifikat_nib_url"],
                proposal_url=file_urls["proposal_url"],
                bmc_url=file_urls["bmc_url"],
                rab_url=file_urls["rab_url"],
                laporan_keuangan_url=file_urls["laporan_keuangan_url"],
                foto_produk_urls=file_urls["foto_produk_urls"],
            )

            self.doc_repo.commit()
            self.doc_repo.refresh(business_doc)

            logger.info(f"Business documents created for tenant {tenant.id}")

            # Prepare response using model's to_dict() method
            tenant_dict = tenant.to_dict()
            tenant_dict["business_documents"] = business_doc.to_dict()

            return create_success_response(
                message="Pendaftaran tenant berhasil dikirim. Menunggu persetujuan admin.",
                data=tenant_dict,
            )

        except Exception as e:
            logger.error(f"Error in register_tenant: {e}", exc_info=True)
            self.tenant_repo.rollback()
            self.doc_repo.rollback()
            return create_error_response(
                message=f"Gagal mendaftar sebagai tenant: {str(e)}"
            )

    def get_tenant_by_user_id(self, user_id: str) -> BaseResponse:
        """Get tenant information by user ID"""
        try:
            tenant = self.tenant_repo.get_by_user_id(user_id)

            if not tenant:
                return create_error_response(message="Tenant tidak ditemukan")

            # Build tenant dict manually to avoid SQLAlchemy relationship issues
            tenant_dict = {
                "id": tenant.id,
                "user_id": tenant.user_id,
                "nama_ketua_tim": tenant.nama_ketua_tim,
                "nim_nidn_ketua": tenant.nim_nidn_ketua,
                "nama_anggota_tim": tenant.nama_anggota_tim,
                "nim_nidn_anggota": tenant.nim_nidn_anggota,
                "nomor_telepon": tenant.nomor_telepon,
                "fakultas": tenant.fakultas,
                "prodi": tenant.prodi,
                "nama_bisnis": tenant.nama_bisnis,
                "kategori_bisnis": tenant.kategori_bisnis,
                "alamat_usaha": tenant.alamat_usaha,
                "jenis_usaha": tenant.jenis_usaha,
                "lama_usaha": tenant.lama_usaha,
                "omzet": tenant.omzet,
                "status": tenant.status.value,
                "rejection_reason": tenant.rejection_reason,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at,
            }

            # Include business documents if exists
            if tenant.business_documents and len(tenant.business_documents) > 0:
                business_doc = tenant.business_documents[0]
                tenant_dict["business_documents"] = {
                    "id": business_doc.id,
                    "tenant_id": business_doc.tenant_id,
                    "logo_url": business_doc.logo_url,
                    "akun_medsos": business_doc.akun_medsos,
                    "sertifikat_nib_url": business_doc.sertifikat_nib_url,
                    "proposal_url": business_doc.proposal_url,
                    "bmc_url": business_doc.bmc_url,
                    "rab_url": business_doc.rab_url,
                    "laporan_keuangan_url": business_doc.laporan_keuangan_url,
                    "foto_produk_urls": business_doc.foto_produk_urls,
                    "created_at": business_doc.created_at,
                    "updated_at": business_doc.updated_at,
                }
            else:
                tenant_dict["business_documents"] = None

            return create_success_response(
                message="Data tenant berhasil diambil",
                data=tenant_dict,
            )

        except Exception as e:
            logger.error(f"Error getting tenant: {e}", exc_info=True)
            return create_error_response(message="Gagal mengambil data tenant")

    def update_tenant_status(
        self,
        tenant_id: str,
        status: str,
        rejection_reason: Optional[str] = None,
    ) -> BaseResponse:
        """
        Update tenant status (admin only).

        Args:
            tenant_id: Tenant ID
            status: New status (approved or rejected)
            rejection_reason: Reason for rejection

        Returns:
            BaseResponse with tenant_id, status, and rejection_reason
        """
        try:
            tenant = self.tenant_repo.get_by_id(tenant_id)

            if not tenant:
                return create_error_response(message="Tenant tidak ditemukan")

            # Convert string to enum
            new_status = TenantStatus(status)

            # Update status
            self.tenant_repo.update_status(tenant, new_status, rejection_reason)
            self.tenant_repo.commit()

            logger.info(f"Tenant {tenant_id} status updated to {status}")

            # If approved, update user role to TENANT
            if new_status == TenantStatus.APPROVED:
                user = self.user_repo.get_by_id(tenant.user_id)
                if user:
                    self.user_repo.update_role(user, UserRole.TENANT)
                    self.user_repo.commit()
                    logger.info(f"User {user.id} role updated to TENANT after approval")
                else:
                    logger.warning(f"User {tenant.user_id} not found for role update")

            # Simple response with only necessary data
            response_data = {
                "tenant_id": tenant_id,
                "status": status,
                "rejection_reason": rejection_reason,
            }

            return create_success_response(
                message=f"Status tenant berhasil diubah menjadi {status}",
                data=response_data,
            )

        except Exception as e:
            logger.error(f"Error updating tenant status: {e}", exc_info=True)
            self.tenant_repo.rollback()
            return create_error_response(message="Gagal mengubah status tenant")

    def get_all_tenants(
        self,
        status: Optional[TenantStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> BaseResponse:
        """
        Get all tenants with optional status filter (admin only).

        Args:
            status: Filter by status (pending, approved, rejected)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            BaseResponse with list of tenants
        """
        try:
            tenants = self.tenant_repo.get_all(status=status, skip=skip, limit=limit)

            tenants_list = []
            for tenant in tenants:
                # Build tenant dict manually
                tenant_dict = {
                    "id": tenant.id,
                    "user_id": tenant.user_id,
                    "nama_ketua_tim": tenant.nama_ketua_tim,
                    "nim_nidn_ketua": tenant.nim_nidn_ketua,
                    "nama_anggota_tim": tenant.nama_anggota_tim,
                    "nim_nidn_anggota": tenant.nim_nidn_anggota,
                    "nomor_telepon": tenant.nomor_telepon,
                    "fakultas": tenant.fakultas,
                    "prodi": tenant.prodi,
                    "nama_bisnis": tenant.nama_bisnis,
                    "kategori_bisnis": tenant.kategori_bisnis,
                    "alamat_usaha": tenant.alamat_usaha,
                    "jenis_usaha": tenant.jenis_usaha,
                    "lama_usaha": tenant.lama_usaha,
                    "omzet": tenant.omzet,
                    "status": tenant.status.value,
                    "rejection_reason": tenant.rejection_reason,
                    "created_at": tenant.created_at,
                    "updated_at": tenant.updated_at,
                }

                # Include business documents if exists
                if tenant.business_documents and len(tenant.business_documents) > 0:
                    business_doc = tenant.business_documents[0]
                    tenant_dict["business_documents"] = {
                        "id": business_doc.id,
                        "tenant_id": business_doc.tenant_id,
                        "logo_url": business_doc.logo_url,
                        "akun_medsos": business_doc.akun_medsos,
                        "sertifikat_nib_url": business_doc.sertifikat_nib_url,
                        "proposal_url": business_doc.proposal_url,
                        "bmc_url": business_doc.bmc_url,
                        "rab_url": business_doc.rab_url,
                        "laporan_keuangan_url": business_doc.laporan_keuangan_url,
                        "foto_produk_urls": business_doc.foto_produk_urls,
                        "created_at": business_doc.created_at,
                        "updated_at": business_doc.updated_at,
                    }
                else:
                    tenant_dict["business_documents"] = None

                tenants_list.append(tenant_dict)

            return create_success_response(
                message=f"Berhasil mengambil {len(tenants_list)} tenant",
                data={
                    "tenants": tenants_list,
                    "total": len(tenants_list),
                    "skip": skip,
                    "limit": limit,
                },
            )

        except Exception as e:
            logger.error(f"Error getting all tenants: {e}", exc_info=True)
            return create_error_response(message="Gagal mengambil data tenant")

    def update_tenant(
        self,
        tenant_id: str,
        user_id: str,
        data: TenantUpdateRequest,
    ) -> BaseResponse:
        """
        Update tenant data.
        
        Args:
            tenant_id: Tenant ID to update
            user_id: User ID making the request (for ownership check)
            data: Update request data
            
        Returns:
            BaseResponse with updated tenant data
        """
        try:
            # Get tenant
            tenant = self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                return create_error_response(message="Tenant tidak ditemukan")
            
            # Check ownership - only the tenant owner can update
            if tenant.user_id != user_id:
                return create_error_response(
                    message="Anda tidak memiliki akses untuk mengubah data tenant ini"
                )
            
            # Check status - only pending and rejected tenants can be updated
            if tenant.status not in [TenantStatus.PENDING, TenantStatus.REJECTED]:
                return create_error_response(
                    message=f"Data tenant dengan status {tenant.status.value} tidak dapat diubah. "
                    f"Hanya tenant dengan status {tenant.status.value} yang dapat diubah."
                )
            
            # Store original status to check if we need to reset
            was_rejected = tenant.status == TenantStatus.REJECTED
            
            # Update tenant data (only non-None fields)
            self.tenant_repo.update(
                tenant=tenant,
                nama_ketua_tim=data.nama_ketua_tim,
                nim_nidn_ketua=data.nim_nidn_ketua,
                nama_anggota_tim=data.nama_anggota_tim,
                nim_nidn_anggota=data.nim_nidn_anggota,
                nomor_telepon=data.nomor_telepon,
                fakultas=data.fakultas,
                prodi=data.prodi,
                nama_bisnis=data.nama_bisnis,
                kategori_bisnis=data.kategori_bisnis,
                alamat_usaha=data.alamat_usaha,
                jenis_usaha=data.jenis_usaha,
                lama_usaha=data.lama_usaha,
                omzet=float(data.omzet) if data.omzet is not None else None,
            )
            
            # Reset status to PENDING if tenant was rejected
            if was_rejected:
                tenant.status = TenantStatus.PENDING
                tenant.rejection_reason = None  # Clear rejection reason
                logger.info(f"Tenant {tenant_id} status reset from REJECTED to PENDING")
            
            # Commit changes
            self.tenant_repo.commit()
            self.tenant_repo.refresh(tenant)
            
            logger.info(f"Tenant {tenant_id} updated successfully by user {user_id}")
            
            # Return updated tenant data
            tenant_data = self._get_tenant_with_documents(tenant)
            
            return create_success_response(
                message="Data tenant berhasil diperbarui",
                data=tenant_data
            )
            
        except Exception as e:
            logger.error(f"Error updating tenant {tenant_id}: {e}", exc_info=True)
            self.tenant_repo.rollback()
            return create_error_response(message="Gagal memperbarui data tenant")

    async def update_tenant_documents(
        self,
        tenant_id: str,
        user_id: str,
        logo: Optional[UploadFile] = None,
        sertifikat_nib: Optional[UploadFile] = None,
        proposal: Optional[UploadFile] = None,
        bmc: Optional[UploadFile] = None,
        rab: Optional[UploadFile] = None,
        laporan_keuangan: Optional[UploadFile] = None,
        foto_produk: Optional[List[UploadFile]] = None,
        akun_medsos: Optional[str] = None,
    ) -> BaseResponse:
        """
        Update tenant documents. Old files will be deleted before uploading new ones.
        
        Args:
            tenant_id: Tenant ID to update
            user_id: User ID making the request (for ownership check)
            logo: New logo file (replaces old one)
            sertifikat_nib: New NIB certificate file
            proposal: New proposal file
            bmc: New BMC file
            rab: New RAB file
            laporan_keuangan: New financial report file
            foto_produk: New product photos
            akun_medsos: Social media accounts JSON string
            
        Returns:
            BaseResponse with updated tenant data
        """
        try:
            # Get tenant
            tenant = self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                return create_error_response(message="Tenant tidak ditemukan")
            
            # Check ownership
            if tenant.user_id != user_id:
                return create_error_response(
                    message="Anda tidak memiliki akses untuk mengubah dokumen tenant ini"
                )
            
            # Check status - only pending and rejected tenants can update documents
            if tenant.status not in [TenantStatus.PENDING, TenantStatus.REJECTED]:
                return create_error_response(
                    message=f"Dokumen tenant dengan status {tenant.status.value} tidak dapat diubah. "
                    "Hanya tenant dengan status pending atau rejected yang dapat diubah."
                )
            
            # Get existing business documents
            business_doc = self.doc_repo.get_by_tenant_id(tenant_id)
            if not business_doc:
                return create_error_response(
                    message="Business documents tidak ditemukan untuk tenant ini"
                )
            
            logger.info(f"Updating documents for tenant {tenant_id}")
            
            # Track which files to delete and new URLs
            files_to_delete = []
            new_urls = {}
            
            # Handle logo update
            if logo and logo.filename:
                if business_doc.logo_url:
                    files_to_delete.append(business_doc.logo_url)
                new_urls["logo_url"] = await file_upload_service.upload_file(
                    logo,
                    folder=f"tenants/{tenant_id}/logos",
                    allowed_extensions=[".jpg", ".jpeg", ".png"],
                    max_size_mb=2
                )
            
            # Handle sertifikat NIB update
            if sertifikat_nib and sertifikat_nib.filename:
                if business_doc.sertifikat_nib_url:
                    files_to_delete.append(business_doc.sertifikat_nib_url)
                new_urls["sertifikat_nib_url"] = await file_upload_service.upload_file(
                    sertifikat_nib,
                    folder=f"tenants/{tenant_id}/documents",
                    allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                    max_size_mb=5
                )
            
            # Handle proposal update
            if proposal and proposal.filename:
                if business_doc.proposal_url:
                    files_to_delete.append(business_doc.proposal_url)
                new_urls["proposal_url"] = await file_upload_service.upload_file(
                    proposal,
                    folder=f"tenants/{tenant_id}/proposals",
                    allowed_extensions=[".pdf", ".doc", ".docx"],
                    max_size_mb=10
                )
            
            # Handle BMC update
            if bmc and bmc.filename:
                if business_doc.bmc_url:
                    files_to_delete.append(business_doc.bmc_url)
                new_urls["bmc_url"] = await file_upload_service.upload_file(
                    bmc,
                    folder=f"tenants/{tenant_id}/documents",
                    allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                    max_size_mb=5
                )
            
            # Handle RAB update
            if rab and rab.filename:
                if business_doc.rab_url:
                    files_to_delete.append(business_doc.rab_url)
                new_urls["rab_url"] = await file_upload_service.upload_file(
                    rab,
                    folder=f"tenants/{tenant_id}/documents",
                    allowed_extensions=[".pdf", ".xls", ".xlsx"],
                    max_size_mb=5
                )
            
            # Handle laporan keuangan update
            if laporan_keuangan and laporan_keuangan.filename:
                if business_doc.laporan_keuangan_url:
                    files_to_delete.append(business_doc.laporan_keuangan_url)
                new_urls["laporan_keuangan_url"] = await file_upload_service.upload_file(
                    laporan_keuangan,
                    folder=f"tenants/{tenant_id}/documents",
                    allowed_extensions=[".pdf", ".xls", ".xlsx"],
                    max_size_mb=10
                )
            
            # Handle foto produk update (multiple files)
            if foto_produk and len(foto_produk) > 0:
                # Delete old product photos if they exist
                if business_doc.foto_produk_urls:
                    try:
                        old_urls = json.loads(business_doc.foto_produk_urls)
                        if isinstance(old_urls, list):
                            files_to_delete.extend(old_urls)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse foto_produk_urls for tenant {tenant_id}")
                
                # Upload new product photos
                foto_urls = await file_upload_service.upload_multiple_files(
                    foto_produk,
                    folder=f"tenants/{tenant_id}/products",
                    allowed_extensions=[".jpg", ".jpeg", ".png"],
                    max_size_mb=5
                )
                new_urls["foto_produk_urls"] = json.dumps(foto_urls)
            
            # Handle akun medsos update
            if akun_medsos is not None:
                new_urls["akun_medsos"] = akun_medsos
            
            # Update business documents in database
            self.doc_repo.update(
                document=business_doc,
                **new_urls
            )
            
            # Reset status to PENDING if tenant was rejected
            if tenant.status == TenantStatus.REJECTED:
                tenant.status = TenantStatus.PENDING
                tenant.rejection_reason = None  # Clear rejection reason
                self.tenant_repo.refresh(tenant)  # Ensure we have latest tenant data
                logger.info(f"Tenant {tenant_id} status reset from REJECTED to PENDING after document update")
            
            # Commit database changes
            self.doc_repo.commit()
            self.doc_repo.refresh(business_doc)
            
            # Delete old files from R2 storage
            deleted_count = 0
            for file_url in files_to_delete:
                if file_upload_service.delete_file(file_url):
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_url}")
                else:
                    logger.warning(f"Failed to delete old file: {file_url}")
            
            logger.info(f"Documents updated for tenant {tenant_id}. Deleted {deleted_count} old files.")
            
            # Refresh tenant to get updated relationships
            self.tenant_repo.refresh(tenant)
            
            # Return updated tenant data
            tenant_data = self._get_tenant_with_documents(tenant)
            
            return create_success_response(
                message=f"Dokumen tenant berhasil diperbarui. {deleted_count} file lama dihapus.",
                data=tenant_data
            )
            
        except Exception as e:
            logger.error(f"Error updating documents for tenant {tenant_id}: {e}", exc_info=True)
            self.doc_repo.rollback()
            return create_error_response(message=f"Gagal memperbarui dokumen tenant: {str(e)}")
