"""
Proposal Classification Routes
Routes untuk klasifikasi proposal menggunakan AI model.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.schema import BaseResponse, create_success_response, create_error_response
from app.core.middleware import get_current_user_firebase_uid
from app.models.dto.proposal_dto import (
    ProposalClassifyFromURLRequest,
    ProposalClassifyFromTextRequest,
    ProposalClassifyFromSectionsRequest,
    ProposalClassificationResult,
)
from app.services.proposal_classifier_service import get_proposal_classifier
from app.services.pdf_parser_service import pdf_parser_service
from app.repositories.tenant_repository import TenantRepository, BusinessDocumentRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposal", tags=["Proposal Classification"])

@router.post("/classify/tenant/{tenant_id}", response_model=BaseResponse)
async def classify_proposal_from_tenant(
    tenant_id: str,
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db),
):
    """
    Klasifikasi proposal berdasarkan tenant_id.

    **Proses:**
    1. Ambil data tenant dari database berdasarkan tenant_id
    2. Ambil proposal_url dari business_documents
    3. Download dan parse PDF dari URL
    4. Klasifikasi dengan model IndoBERT
    5. Return hasil: PASS atau REJECT

    **Path Parameter:**
    - tenant_id: ID tenant yang akan diklasifikasi proposalnya

    **Returns:**
    ```json
    {
        "status": "success",
        "message": "Proposal berhasil diklasifikasi",
        "data": {
            "tenant_id": "A1B2",
            "nama_bisnis": "Bisnis ABC",
            "proposal_url": "https://storage.example.com/proposals/proposal_001.pdf",
            "classification": {
                "prediction": "pass",
                "confidence": 0.9543,
                "label": 1,
                "message": "PASS - Proposal memenuhi kriteria administrasi dan substansi",
                "proposal_text_length": 1250
            }
        }
    }
    ```

    **Requires authentication:**
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    try:
        # Get tenant data
        tenant_repo = TenantRepository(db)
        tenant = tenant_repo.get_by_id(tenant_id)

        if not tenant:
            return create_error_response(
                message=f"Tenant dengan ID {tenant_id} tidak ditemukan"
            )

        # Get business documents
        if not tenant.business_documents or len(tenant.business_documents) == 0:
            return create_error_response(
                message=f"Tenant {tenant_id} belum memiliki dokumen bisnis"
            )

        business_doc = tenant.business_documents[0]

        if not business_doc.proposal_url:
            return create_error_response(
                message=f"Tenant {tenant_id} belum mengupload proposal"
            )

        logger.info(
            f"Classifying proposal for tenant {tenant_id}: {business_doc.proposal_url}"
        )

        try:
            proposal_text = await pdf_parser_service.parse_pdf_from_url(
                business_doc.proposal_url, extract_sections=True
            )
        except Exception as parse_error:
            logger.error(f"Error parsing PDF: {parse_error}", exc_info=True)
            return create_error_response(
                message=f"Gagal parsing PDF: {str(parse_error)}"
            )

        if not proposal_text:
            logger.error(f"PDF parsing returned empty text for tenant {tenant_id}")
            return create_error_response(
                message="Gagal mengekstrak teks dari PDF. Kemungkinan penyebab: "
                "1) PDF tidak dapat diakses dari URL, "
                "2) PDF kosong atau corrupt, "
                "3) Format PDF tidak didukung. "
                "Silakan coba upload ulang proposal dalam format PDF yang valid."
            )

        if len(proposal_text.strip()) < 50:
            return create_error_response(
                message="Teks proposal terlalu pendek. Minimal 50 karakter diperlukan."
            )

        # Klasifikasi
        classifier = get_proposal_classifier()
        classification_result = classifier.classify_proposal(proposal_text)

        # Tambahkan info panjang text
        classification_result["proposal_text_length"] = len(proposal_text)

        # Build response dengan info tenant
        response_data = {
            "tenant_id": tenant.id,
            "nama_bisnis": tenant.nama_bisnis,
            "nama_ketua_tim": tenant.nama_ketua_tim,
            "proposal_url": business_doc.proposal_url,
            "classification": classification_result,
        }

        return create_success_response(
            message="Proposal berhasil diklasifikasi", data=response_data
        )

    except Exception as e:
        logger.error(
            f"Error klasifikasi proposal untuk tenant {tenant_id}: {e}", exc_info=True
        )
        return create_error_response(
            message=f"Gagal melakukan klasifikasi: {str(e)}"
        )

