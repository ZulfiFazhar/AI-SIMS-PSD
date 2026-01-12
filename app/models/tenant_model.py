"""
Tenant and BusinessDocument models for tenant registration.
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, Integer, DECIMAL, Text, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from app.core.database import Base


class TenantStatus(str, enum.Enum):
    """
    Tenant registration status.
    - PENDING: Awaiting approval from admin
    - APPROVED: Registration approved, user becomes tenant
    - REJECTED: Registration rejected by admin
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Tenant(Base):
    """
    Tenant model for storing tenant registration data.
    One-to-one relationship with User.
    """

    __tablename__ = "tenants"

    id = Column(CHAR(4), primary_key=True, index=True)
    user_id = Column(CHAR(4), ForeignKey("users.id"), nullable=False, unique=True)

    # Team information
    nama_ketua_tim = Column(String(255), nullable=False)
    nim_nidn_ketua = Column(String(50), nullable=False)
    nama_anggota_tim = Column(String(255), nullable=True)
    nim_nidn_anggota = Column(String(50), nullable=True)
    nomor_telepon = Column(String(20), nullable=False)

    # Academic information
    fakultas = Column(String(100), nullable=False)
    prodi = Column(String(100), nullable=False)

    # Business information
    nama_bisnis = Column(String(255), nullable=False)
    kategori_bisnis = Column(String(100), nullable=False)
    alamat_usaha = Column(Text, nullable=False)
    jenis_usaha = Column(String(100), nullable=False)
    lama_usaha = Column(Integer, nullable=False)  # dalam bulan
    omzet = Column(DECIMAL(15, 2), nullable=False)

    # Status
    status = Column(
        Enum(TenantStatus),
        default=TenantStatus.PENDING,
        nullable=False,
        server_default="pending",
    )
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    business_documents = relationship(
        "BusinessDocument", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Tenant(id={self.id}, user_id={self.user_id}, nama_bisnis={self.nama_bisnis})>"

    def to_dict(self):
        """Convert tenant object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "nama_ketua_tim": self.nama_ketua_tim,
            "nim_nidn_ketua": self.nim_nidn_ketua,
            "nama_anggota_tim": self.nama_anggota_tim,
            "nim_nidn_anggota": self.nim_nidn_anggota,
            "nomor_telepon": self.nomor_telepon,
            "fakultas": self.fakultas,
            "prodi": self.prodi,
            "nama_bisnis": self.nama_bisnis,
            "kategori_bisnis": self.kategori_bisnis,
            "alamat_usaha": self.alamat_usaha,
            "jenis_usaha": self.jenis_usaha,
            "lama_usaha": self.lama_usaha,
            "omzet": float(self.omzet) if self.omzet else None,
            "status": self.status.value if isinstance(self.status, TenantStatus) else self.status,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BusinessDocument(Base):
    """
    Business documents model for storing uploaded files.
    One-to-one relationship with Tenant.
    """

    __tablename__ = "business_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(CHAR(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Document URLs (stored in Cloudflare R2)
    logo_url = Column(String(500), nullable=True)
    akun_medsos = Column(Text, nullable=True)  # JSON string
    sertifikat_nib_url = Column(String(500), nullable=True)
    proposal_url = Column(String(500), nullable=True)
    bmc_url = Column(String(500), nullable=True)
    rab_url = Column(String(500), nullable=True)
    laporan_keuangan_url = Column(String(500), nullable=True)
    foto_produk_urls = Column(Text, nullable=True)  # JSON array of URLs

    # Timestamps
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="business_documents")

    def __repr__(self):
        return f"<BusinessDocument(id={self.id}, tenant_id={self.tenant_id})>"

    def to_dict(self):
        """Convert business document object to dictionary"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "logo_url": self.logo_url,
            "akun_medsos": self.akun_medsos,
            "sertifikat_nib_url": self.sertifikat_nib_url,
            "proposal_url": self.proposal_url,
            "bmc_url": self.bmc_url,
            "rab_url": self.rab_url,
            "laporan_keuangan_url": self.laporan_keuangan_url,
            "foto_produk_urls": self.foto_produk_urls,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
