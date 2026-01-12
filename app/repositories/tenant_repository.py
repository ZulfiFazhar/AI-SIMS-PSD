"""
Tenant repository for database operations.
Handles all database queries related to Tenant and BusinessDocument models.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload

from app.models.tenant_model import Tenant, BusinessDocument, TenantStatus
from app.core.utils import generate_short_id

logger = logging.getLogger(__name__)


class TenantRepository:
    """Repository for Tenant database operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return (
            self.db.query(Tenant)
            .options(joinedload(Tenant.business_documents))
            .filter(Tenant.id == tenant_id)
            .first()
        )

    def get_by_user_id(self, user_id: str) -> Optional[Tenant]:
        """Get tenant by user ID"""
        return (
            self.db.query(Tenant)
            .options(joinedload(Tenant.business_documents))
            .filter(Tenant.user_id == user_id)
            .first()
        )

    def get_all(
        self, status: Optional[TenantStatus] = None, skip: int = 0, limit: int = 100
    ) -> List[Tenant]:
        """
        Get all tenants with optional status filter.

        Args:
            status: Filter by status (pending, approved, rejected)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Tenant objects
        """
        query = self.db.query(Tenant).options(joinedload(Tenant.business_documents))

        if status:
            query = query.filter(Tenant.status == status)

        return query.offset(skip).limit(limit).all()

    def create(
        self,
        user_id: str,
        nama_ketua_tim: str,
        nim_nidn_ketua: str,
        nomor_telepon: str,
        fakultas: str,
        prodi: str,
        nama_bisnis: str,
        kategori_bisnis: str,
        alamat_usaha: str,
        jenis_usaha: str,
        lama_usaha: int,
        omzet: float,
        nama_anggota_tim: Optional[str] = None,
        nim_nidn_anggota: Optional[str] = None,
    ) -> Tenant:
        """
        Create a new tenant with unique ID generation.

        Args:
            user_id: User ID
            nama_ketua_tim: Team leader name
            nim_nidn_ketua: Team leader NIM/NIDN
            nomor_telepon: Phone number
            fakultas: Faculty
            prodi: Study program
            nama_bisnis: Business name
            kategori_bisnis: Business category
            alamat_usaha: Business address
            jenis_usaha: Business type
            lama_usaha: Business duration in months
            omzet: Business revenue
            nama_anggota_tim: Team member name (optional)
            nim_nidn_anggota: Team member NIM/NIDN (optional)

        Returns:
            Created Tenant object

        Raises:
            Exception: If unable to generate unique ID after max retries
        """
        # Generate unique ID with collision check
        max_retries = 10
        tenant_id = None

        for attempt in range(max_retries):
            tenant_id = "TN" + generate_short_id(2)  # TN + 2 chars = TN01, TN02, etc.
            existing = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not existing:
                break
            if attempt == max_retries - 1:
                logger.error("Failed to generate unique tenant ID after max retries")
                raise Exception("Failed to generate unique tenant ID")

        tenant = Tenant(
            id=tenant_id,
            user_id=user_id,
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
            status=TenantStatus.PENDING,
        )

        self.db.add(tenant)
        return tenant

    def update_status(
        self,
        tenant: Tenant,
        status: TenantStatus,
        rejection_reason: Optional[str] = None,
    ) -> Tenant:
        """
        Update tenant status.

        Args:
            tenant: Tenant object to update
            status: New status
            rejection_reason: Reason for rejection (if status is rejected)

        Returns:
            Updated Tenant object
        """
        tenant.status = status
        tenant.rejection_reason = rejection_reason
        tenant.updated_at = datetime.now(timezone.utc)
        return tenant

    def commit(self):
        """Commit database transaction"""
        self.db.commit()

    def rollback(self):
        """Rollback database transaction"""
        self.db.rollback()

    def refresh(self, tenant: Tenant):
        """Refresh tenant object from database"""
        self.db.refresh(tenant)


class BusinessDocumentRepository:
    """Repository for BusinessDocument database operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_tenant_id(self, tenant_id: str) -> Optional[BusinessDocument]:
        """Get business documents by tenant ID"""
        return (
            self.db.query(BusinessDocument)
            .filter(BusinessDocument.tenant_id == tenant_id)
            .first()
        )

    def create(
        self,
        tenant_id: str,
        logo_url: Optional[str] = None,
        akun_medsos: Optional[str] = None,
        sertifikat_nib_url: Optional[str] = None,
        proposal_url: Optional[str] = None,
        bmc_url: Optional[str] = None,
        rab_url: Optional[str] = None,
        laporan_keuangan_url: Optional[str] = None,
        foto_produk_urls: Optional[str] = None,
    ) -> BusinessDocument:
        """
        Create business documents.

        Args:
            tenant_id: Tenant ID
            logo_url: Logo file URL
            akun_medsos: Social media accounts (JSON string)
            sertifikat_nib_url: NIB certificate URL
            proposal_url: Proposal file URL
            bmc_url: BMC file URL
            rab_url: RAB file URL
            laporan_keuangan_url: Financial report URL
            foto_produk_urls: Product photos URLs (JSON array string)

        Returns:
            Created BusinessDocument object
        """
        document = BusinessDocument(
            tenant_id=tenant_id,
            logo_url=logo_url,
            akun_medsos=akun_medsos,
            sertifikat_nib_url=sertifikat_nib_url,
            proposal_url=proposal_url,
            bmc_url=bmc_url,
            rab_url=rab_url,
            laporan_keuangan_url=laporan_keuangan_url,
            foto_produk_urls=foto_produk_urls,
        )

        self.db.add(document)
        return document

    def update(
        self,
        document: BusinessDocument,
        logo_url: Optional[str] = None,
        akun_medsos: Optional[str] = None,
        sertifikat_nib_url: Optional[str] = None,
        proposal_url: Optional[str] = None,
        bmc_url: Optional[str] = None,
        rab_url: Optional[str] = None,
        laporan_keuangan_url: Optional[str] = None,
        foto_produk_urls: Optional[str] = None,
    ) -> BusinessDocument:
        """Update business documents"""
        if logo_url is not None:
            document.logo_url = logo_url
        if akun_medsos is not None:
            document.akun_medsos = akun_medsos
        if sertifikat_nib_url is not None:
            document.sertifikat_nib_url = sertifikat_nib_url
        if proposal_url is not None:
            document.proposal_url = proposal_url
        if bmc_url is not None:
            document.bmc_url = bmc_url
        if rab_url is not None:
            document.rab_url = rab_url
        if laporan_keuangan_url is not None:
            document.laporan_keuangan_url = laporan_keuangan_url
        if foto_produk_urls is not None:
            document.foto_produk_urls = foto_produk_urls

        document.updated_at = datetime.now(timezone.utc)
        return document

    def commit(self):
        """Commit database transaction"""
        self.db.commit()

    def rollback(self):
        """Rollback database transaction"""
        self.db.rollback()

    def refresh(self, document: BusinessDocument):
        """Refresh business document object from database"""
        self.db.refresh(document)
