"""
Proposal DTO
Data Transfer Objects untuk klasifikasi proposal.
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


class ProposalClassifyFromURLRequest(BaseModel):
    """Request untuk klasifikasi proposal dari URL"""

    proposal_url: str = Field(
        ...,
        description="URL file PDF proposal yang akan diklasifikasi",
        examples=["https://storage.example.com/proposals/proposal_001.pdf"],
    )


class ProposalClassifyFromTextRequest(BaseModel):
    """Request untuk klasifikasi proposal dari text langsung"""

    proposal_text: str = Field(
        ...,
        description="Teks proposal lengkap yang akan diklasifikasi",
        min_length=50,
    )


class ProposalClassifyFromSectionsRequest(BaseModel):
    """Request untuk klasifikasi proposal dari sections terpisah"""

    latar_belakang: str = Field(default="", description="Teks latar belakang")
    noble_purpose: str = Field(default="", description="Teks noble purpose")
    konsumen: str = Field(default="", description="Teks konsumen")
    produk_inovatif: str = Field(default="", description="Teks produk inovatif")
    strategi_pemasaran: str = Field(
        default="", description="Teks strategi pemasaran"
    )
    sumber_daya: str = Field(default="", description="Teks sumber daya")
    keuangan_narrative: str = Field(default="", description="Teks keuangan")
    rab_narrative: str = Field(default="", description="Teks RAB")


class ProposalClassificationResult(BaseModel):
    """Response hasil klasifikasi proposal"""

    prediction: str = Field(
        ...,
        description="Hasil prediksi: 'pass' atau 'reject'",
        examples=["pass", "reject"],
    )
    confidence: float = Field(
        ...,
        description="Tingkat kepercayaan model (0-1)",
        ge=0.0,
        le=1.0,
        examples=[0.9543],
    )
    label: int = Field(
        ..., description="Label numerik: 1 untuk pass, 0 untuk reject", examples=[1, 0]
    )
    message: str = Field(
        ...,
        description="Pesan penjelasan hasil klasifikasi",
        examples=["PASS - Proposal memenuhi kriteria administrasi dan substansi"],
    )
    proposal_text_length: Optional[int] = Field(
        None, description="Panjang teks proposal yang dianalisis"
    )


class TenantProposalClassificationResult(BaseModel):
    """Response hasil klasifikasi proposal berdasarkan tenant_id"""

    tenant_id: str = Field(..., description="ID tenant", examples=["A1B2"])
    nama_bisnis: str = Field(
        ..., description="Nama bisnis tenant", examples=["Bisnis ABC"]
    )
    nama_ketua_tim: str = Field(
        ..., description="Nama ketua tim tenant", examples=["John Doe"]
    )
    proposal_url: str = Field(
        ...,
        description="URL proposal yang diklasifikasi",
        examples=["https://storage.example.com/proposals/proposal_001.pdf"],
    )
    classification: ProposalClassificationResult = Field(
        ..., description="Hasil klasifikasi proposal"
    )
