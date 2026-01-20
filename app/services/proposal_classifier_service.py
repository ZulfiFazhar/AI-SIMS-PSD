"""
Proposal Classifier Service
Service untuk load model IndoBERT dan melakukan klasifikasi proposal.
Berdasarkan model yang telah di-fine-tune di notebook 4_Finetuning.ipynb
"""

import logging
import os
from typing import Optional, Dict, Any
import torch
from transformers import BertForSequenceClassification, BertTokenizer

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProposalClassifierService:
    """Service untuk klasifikasi proposal menggunakan IndoBERT fine-tuned model"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_path = os.path.join(
            settings.base_dir, "app", "ml", "indobert_full_proposal_finetuned"
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        """Load model dan tokenizer dari disk"""
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"Model path tidak ditemukan: {self.model_path}")
                raise FileNotFoundError(
                    f"Model tidak ditemukan di {self.model_path}. "
                    "Pastikan model sudah di-train dan disimpan."
                )

            logger.info(f"Loading model dari: {self.model_path}")
            self.model = BertForSequenceClassification.from_pretrained(self.model_path)
            self.tokenizer = BertTokenizer.from_pretrained(self.model_path)

            # Move model to device
            self.model.to(self.device)
            self.model.eval()  # Set ke evaluation mode

            logger.info(f"Model berhasil di-load pada device: {self.device}")

        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            raise

    def classify_proposal(self, proposal_text: str) -> Dict[str, Any]:
        """
        Klasifikasi proposal text menggunakan model.

        Args:
            proposal_text: Teks proposal yang akan diklasifikasi

        Returns:
            Dictionary dengan hasil klasifikasi:
            {
                "prediction": "pass" atau "reject",
                "confidence": float (0-1),
                "label": int (1 untuk pass, 0 untuk reject),
                "message": string penjelasan hasil
            }
        """
        try:
            if not proposal_text or len(proposal_text.strip()) == 0:
                return {
                    "prediction": "reject",
                    "confidence": 1.0,
                    "label": 0,
                    "message": "Proposal kosong atau tidak valid",
                }

            # Tokenize input
            inputs = self.tokenizer(
                proposal_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )

            # Move inputs to same device as model
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

                # Get prediction dan confidence
                probabilities = torch.softmax(logits, dim=1)
                prediction_label = torch.argmax(logits, dim=1).item()
                confidence = probabilities[0][prediction_label].item()

            # Map prediction ke status
            if prediction_label == 1:
                prediction = "pass"
                message = "PASS - Proposal memenuhi kriteria administrasi dan substansi"
            else:
                prediction = "reject"
                message = "REJECT - Proposal tidak memenuhi kriteria atau deskripsi kurang lengkap"

            result = {
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "label": prediction_label,
                "message": message,
            }

            logger.info(
                f"Klasifikasi selesai: {prediction} (confidence: {confidence:.2%})"
            )
            return result

        except Exception as e:
            logger.error(f"Error dalam klasifikasi proposal: {e}", exc_info=True)
            return {
                "prediction": "reject",
                "confidence": 0.0,
                "label": 0,
                "message": f"Error klasifikasi: {str(e)}",
            }

    def classify_proposal_sections(
        self,
        latar_belakang: str = "",
        noble_purpose: str = "",
        konsumen: str = "",
        produk_inovatif: str = "",
        strategi_pemasaran: str = "",
        sumber_daya: str = "",
        keuangan_narrative: str = "",
        rab_narrative: str = "",
    ) -> Dict[str, Any]:
        """
        Klasifikasi proposal berdasarkan section-section terpisah.
        Menggabungkan semua section menjadi satu teks sebelum klasifikasi.

        Args:
            latar_belakang: Teks latar belakang
            noble_purpose: Teks noble purpose
            konsumen: Teks konsumen
            produk_inovatif: Teks produk inovatif
            strategi_pemasaran: Teks strategi pemasaran
            sumber_daya: Teks sumber daya
            keuangan_narrative: Teks keuangan
            rab_narrative: Teks RAB

        Returns:
            Dictionary dengan hasil klasifikasi
        """
        # Gabungkan semua section menjadi satu teks
        sections = [
            latar_belakang,
            noble_purpose,
            konsumen,
            produk_inovatif,
            strategi_pemasaran,
            sumber_daya,
            keuangan_narrative,
            rab_narrative,
        ]

        full_text = " ".join([s.strip() for s in sections if s])

        return self.classify_proposal(full_text)

    def reload_model(self):
        """Reload model dari disk (berguna jika model di-update)"""
        logger.info("Reloading model...")
        self._load_model()


# Singleton instance - will be initialized on first import
# Ini memastikan model hanya di-load sekali di memory
_classifier_instance = None


def get_proposal_classifier() -> ProposalClassifierService:
    """Get singleton instance of ProposalClassifierService"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ProposalClassifierService()
    return _classifier_instance
