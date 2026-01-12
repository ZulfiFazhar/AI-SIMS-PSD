import logging
import json
from typing import List, Optional
from fastapi import UploadFile

from app.models.tenant_model import TenantStatus
from app.models.dto.tenant_dto import (
    TenantRegisterRequest,
    TenantResponse,
    BusinessDocumentResponse,
)
from app.repositories.tenant_repository import (
    TenantRepository,
    BusinessDocumentRepository,
)
from app.services.file_upload_service import file_upload_service
from app.core.schema import BaseResponse, create_success_response, create_error_response

logger = logging.getLogger(__name__)


class TenantService:
    """Service class for tenant business logic"""

    def __init__(
        self,
        tenant_repository: TenantRepository,
        business_document_repository: BusinessDocumentRepository,
    ):
        self.tenant_repo = tenant_repository
        self.doc_repo = business_document_repository

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
            data: Tenant registration data
            logo: Logo file
            sertifikat_nib: NIB certificate file
            proposal: Proposal file
            bmc: BMC file
            rab: RAB file
            laporan_keuangan: Financial report file
            foto_produk: List of product photo files

        Returns:
            BaseResponse with TenantResponse data
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
            logo_url = None
            sertifikat_nib_url = None
            proposal_url = None
            bmc_url = None
            rab_url = None
            laporan_keuangan_url = None
            foto_produk_urls = None

            try:
                # Upload logo
                if logo and logo.filename:
                    logger.info(f"Uploading logo: {logo.filename}")
                    logo_url = await file_upload_service.upload_file(
                        logo,
                        folder=f"tenants/{tenant.id}/logos",
                        allowed_extensions=[".jpg", ".jpeg", ".png"],
                        max_size_mb=2,
                    )
                    logger.info(f"Logo uploaded successfully: {logo_url}")

                # Upload sertifikat NIB
                if sertifikat_nib and sertifikat_nib.filename:
                    logger.info(f"Uploading sertifikat NIB: {sertifikat_nib.filename}")
                    sertifikat_nib_url = await file_upload_service.upload_file(
                        sertifikat_nib,
                        folder=f"tenants/{tenant.id}/documents",
                        allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                        max_size_mb=5,
                    )
                    logger.info(
                        f"Sertifikat NIB uploaded successfully: {sertifikat_nib_url}"
                    )

                # Upload proposal
                if proposal and proposal.filename:
                    logger.info(f"Uploading proposal: {proposal.filename}")
                    proposal_url = await file_upload_service.upload_file(
                        proposal,
                        folder=f"tenants/{tenant.id}/documents",
                        allowed_extensions=[".pdf", ".doc", ".docx"],
                        max_size_mb=10,
                    )
                    logger.info(f"Proposal uploaded successfully: {proposal_url}")

                # Upload BMC
                if bmc and bmc.filename:
                    logger.info(f"Uploading BMC: {bmc.filename}")
                    bmc_url = await file_upload_service.upload_file(
                        bmc,
                        folder=f"tenants/{tenant.id}/documents",
                        allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"],
                        max_size_mb=5,
                    )
                    logger.info(f"BMC uploaded successfully: {bmc_url}")

                # Upload RAB
                if rab and rab.filename:
                    logger.info(f"Uploading RAB: {rab.filename}")
                    rab_url = await file_upload_service.upload_file(
                        rab,
                        folder=f"tenants/{tenant.id}/documents",
                        allowed_extensions=[".pdf", ".xls", ".xlsx"],
                        max_size_mb=5,
                    )
                    logger.info(f"RAB uploaded successfully: {rab_url}")

                # Upload laporan keuangan
                if laporan_keuangan and laporan_keuangan.filename:
                    logger.info(
                        f"Uploading laporan keuangan: {laporan_keuangan.filename}"
                    )
                    laporan_keuangan_url = await file_upload_service.upload_file(
                        laporan_keuangan,
                        folder=f"tenants/{tenant.id}/documents",
                        allowed_extensions=[".pdf", ".xls", ".xlsx"],
                        max_size_mb=10,
                    )
                    logger.info(
                        f"Laporan keuangan uploaded successfully: {laporan_keuangan_url}"
                    )

                # Upload foto produk (multiple files)
                if foto_produk and len(foto_produk) > 0:
                    logger.info(f"Uploading {len(foto_produk)} foto produk")
                    foto_urls = await file_upload_service.upload_multiple_files(
                        [f for f in foto_produk if f.filename],
                        folder=f"tenants/{tenant.id}/products",
                        allowed_extensions=[".jpg", ".jpeg", ".png"],
                        max_size_mb=5,
                    )
                    if foto_urls:
                        foto_produk_urls = json.dumps(foto_urls)
                        logger.info(
                            f"Foto produk uploaded successfully: {len(foto_urls)} files"
                        )

            except Exception as upload_error:
                logger.error(
                    f"File upload error: {type(upload_error).__name__} - {str(upload_error)}",
                    exc_info=True,
                )
                # Continue without failing the registration
                # Files can be uploaded later

            # Create business documents record
            business_doc = self.doc_repo.create(
                tenant_id=tenant.id,
                logo_url=logo_url,
                akun_medsos=data.akun_medsos,
                sertifikat_nib_url=sertifikat_nib_url,
                proposal_url=proposal_url,
                bmc_url=bmc_url,
                rab_url=rab_url,
                laporan_keuangan_url=laporan_keuangan_url,
                foto_produk_urls=foto_produk_urls,
            )

            self.doc_repo.commit()
            self.doc_repo.refresh(business_doc)

            logger.info(f"Business documents created for tenant {tenant.id}")

            # Prepare response
            tenant_response = TenantResponse.model_validate(tenant)
            tenant_response.business_documents = (
                BusinessDocumentResponse.model_validate(business_doc)
            )

            return create_success_response(
                message="Pendaftaran tenant berhasil dikirim. Menunggu persetujuan admin.",
                data=tenant_response.model_dump(),
            )

        except Exception as e:
            logger.error(f"Error in register_tenant: {e}")
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

            tenant_response = TenantResponse.model_validate(tenant)

            # Include business documents if exists
            if tenant.business_documents:
                tenant_response.business_documents = (
                    BusinessDocumentResponse.model_validate(
                        tenant.business_documents[0]
                    )
                )

            return create_success_response(
                message="Data tenant berhasil diambil",
                data=tenant_response.model_dump(),
            )

        except Exception as e:
            logger.error(f"Error getting tenant: {e}")
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
            BaseResponse with updated tenant data
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
            self.tenant_repo.refresh(tenant)

            logger.info(f"Tenant {tenant_id} status updated to {status}")

            tenant_response = TenantResponse.model_validate(tenant)

            return create_success_response(
                message=f"Status tenant berhasil diubah menjadi {status}",
                data=tenant_response.model_dump(),
            )

        except Exception as e:
            logger.error(f"Error updating tenant status: {e}")
            self.tenant_repo.rollback()
            return create_error_response(message="Gagal mengubah status tenant")

    async def upload_business_document(
        self,
        file: UploadFile,
    ) -> str:
        """
        Upload business document file for tenant.

        Args:
            file: FastAPI UploadFile object
        Returns:
            Public URL of the uploaded file
        """
        try:
            url = await file_upload_service.upload_file(
                file,
                folder="tenants/business_documents",
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
            return url
        except Exception as e:
            logger.error(f"Error uploading business document: {e}")
            raise

    async def upload_multiple_business_documents(
        self,
        files: List[UploadFile],
    ) -> List[str]:
        """
        Upload multiple business document files for tenant.

        Args:
            files: List of FastAPI UploadFile objects
        Returns:
            List of public URLs of the uploaded files
        """
        try:
            urls = await file_upload_service.upload_multiple_files(
                files,
                folder="tenants/business_documents",
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
            return urls
        except Exception as e:
            logger.error(f"Error uploading multiple business documents: {e}")
            raise
