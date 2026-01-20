import logging
import tempfile
import os
import re
from typing import Optional, Dict
import httpx

logger = logging.getLogger(__name__)


class ProposalParser:
    """Parser untuk mengekstrak section-section spesifik dari proposal PDF"""

    def __init__(self):
        # Mapping Heading di PDF ke Nama Kolom Database
        self.section_map = {
            r"1\.1\s+Latar\s+Belakang\s+Usaha": "txt_latar_belakang",
            r"2\.1\s+Noble\s+Purpose": "txt_noble_purpose",
            r"2\.2\s+Identifikasi\s+Konsumen": "txt_konsumen",
            r"2\.3\s+Produk\s+Inovatif": "txt_produk_inovatif",
            r"2\.4\s+Strategi\s+Pemasaran": "txt_strategi_pemasaran",
            r"2\.5\s+Sumber\s+Daya": "txt_sumber_daya",
            r"3\.1\s+Laporan/Proyeksi\s+Keuangan": "txt_keuangan_narrative",
            r"3\.2\s+Rencana\s+Anggaran\s+Belanja": "txt_rab_narrative",
        }

        # Urutan section untuk logika pengambilan teks (Start -> End)
        self.section_order = [
            "txt_latar_belakang",
            "txt_noble_purpose",
            "txt_konsumen",
            "txt_produk_inovatif",
            "txt_strategi_pemasaran",
            "txt_sumber_daya",
            "txt_keuangan_narrative",
            "txt_rab_narrative",
        ]

    def parse_sections(self, full_text: str) -> Dict[str, str]:
        """
        Parse full text menjadi sections berdasarkan regex pattern.

        Args:
            full_text: Teks lengkap dari PDF

        Returns:
            Dictionary dengan key = section name, value = section text
        """
        sections = {key: "" for key in self.section_order}

        # Cari posisi semua heading dalam teks
        heading_positions = []
        for pattern, section_name in self.section_map.items():
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                heading_positions.append(
                    {
                        "position": match.start(),
                        "section_name": section_name,
                        "heading_text": match.group(),
                    }
                )

        # Sort berdasarkan posisi
        heading_positions.sort(key=lambda x: x["position"])

        # Log sections yang ditemukan
        if heading_positions:
            logger.info(f"Found {len(heading_positions)} section headings in PDF")
            for hp in heading_positions:
                logger.debug(f"  - {hp['heading_text']} at position {hp['position']}")
        else:
            logger.warning("No section headings found in PDF text")

        # Extract text untuk setiap section (dari heading sampai heading berikutnya)
        for i, heading in enumerate(heading_positions):
            section_name = heading["section_name"]
            start_pos = heading["position"] + len(heading["heading_text"])

            # Tentukan end position (mulai dari heading berikutnya atau akhir teks)
            if i + 1 < len(heading_positions):
                end_pos = heading_positions[i + 1]["position"]
            else:
                end_pos = len(full_text)

            # Extract dan clean text
            section_text = full_text[start_pos:end_pos].strip()

            # Remove excessive whitespace dan newlines
            section_text = re.sub(r"\s+", " ", section_text)

            sections[section_name] = section_text

        logger.info(
            f"Parsed {len([s for s in sections.values() if s])} sections from proposal"
        )

        return sections

    def get_full_proposal_text(self, sections: Dict[str, str]) -> str:
        """
        Gabungkan semua sections menjadi satu teks lengkap.

        Args:
            sections: Dictionary sections dari parse_sections()

        Returns:
            Teks proposal lengkap yang digabung
        """
        full_text = " ".join(
            [sections[key] for key in self.section_order if sections.get(key)]
        )
        return full_text.strip()


class PDFParserService:
    """Service untuk parsing PDF proposal"""

    def __init__(self):
        self.timeout = 30.0  # Timeout untuk download file
        self.proposal_parser = ProposalParser()

    async def parse_pdf_from_url(
        self, pdf_url: str, extract_sections: bool = False
    ) -> Optional[str]:
        """
        Parse PDF dari URL dan ekstrak teks.

        Args:
            pdf_url: URL file PDF
            extract_sections: Jika True, hanya extract sections spesifik.
                            Jika False, extract semua teks.

        Returns:
            Teks yang diekstrak dari PDF atau None jika gagal
        """
        try:
            # Download PDF dari URL
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()

            # Simpan ke temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            # Parse PDF
            full_text = self._extract_text_from_pdf(tmp_path)
            
            logger.info(f"Extracted {len(full_text)} characters from PDF")

            # Hapus temporary file
            os.unlink(tmp_path)

            # Check if full_text is empty
            if not full_text or len(full_text.strip()) == 0:
                logger.error("PDF extraction resulted in empty text")
                return None

            # Jika extract_sections=True, parse sections dan gabungkan
            if extract_sections:
                sections = self.proposal_parser.parse_sections(full_text)
                sections_with_content = [s for s in sections.values() if s]
                
                logger.info(
                    f"Extracted sections from PDF. Total sections with content: {len(sections_with_content)}"
                )
                
                # Gabungkan sections
                text = self.proposal_parser.get_full_proposal_text(sections)
                
                # Fallback ke full text jika sections kosong
                if not text or len(text.strip()) < 100:
                    logger.warning(
                        f"Section extraction resulted in insufficient text ({len(text) if text else 0} chars). "
                        "Falling back to full PDF text."
                    )
                    text = full_text
            else:
                text = full_text

            return text

        except httpx.HTTPError as e:
            logger.error(f"HTTP error saat download PDF: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}", exc_info=True)
            return None

    async def parse_pdf_sections_from_url(
        self, pdf_url: str
    ) -> Optional[Dict[str, str]]:
        """
        Parse PDF dari URL dan ekstrak sections terstruktur.

        Args:
            pdf_url: URL file PDF

        Returns:
            Dictionary dengan section names dan texts, atau None jika gagal
        """
        try:
            # Download PDF dari URL
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()

            # Simpan ke temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            # Parse PDF
            full_text = self._extract_text_from_pdf(tmp_path)

            # Hapus temporary file
            os.unlink(tmp_path)

            # Parse sections
            sections = self.proposal_parser.parse_sections(full_text)

            return sections

        except httpx.HTTPError as e:
            logger.error(f"HTTP error saat download PDF: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing PDF sections: {e}", exc_info=True)
            return None

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Ekstrak teks dari file PDF menggunakan PyPDF atau pdfplumber.

        Args:
            pdf_path: Path ke file PDF

        Returns:
            Teks yang diekstrak dari PDF
        """
        text = ""

        try:
            # Try pdfplumber first (better for complex PDFs)
            import pdfplumber

            logger.debug(f"Extracting text from PDF using pdfplumber: {pdf_path}")
            with pdfplumber.open(pdf_path) as pdf:
                logger.debug(f"PDF has {len(pdf.pages)} pages")
                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        logger.debug(f"Extracted {len(page_text)} chars from page {i}")

        except ImportError:
            logger.info("pdfplumber not available, falling back to pypdf")
            try:
                # Fallback to pypdf
                from pypdf import PdfReader

                logger.debug(f"Extracting text from PDF using pypdf: {pdf_path}")
                reader = PdfReader(pdf_path)
                logger.debug(f"PDF has {len(reader.pages)} pages")
                for i, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        logger.debug(f"Extracted {len(page_text)} chars from page {i}")

            except ImportError:
                logger.error("Neither pdfplumber nor pypdf is installed")
                raise ImportError(
                    "Please install pdfplumber or pypdf: pip install pdfplumber pypdf"
                )

        return text.strip()

    def parse_pdf_from_file(
        self, pdf_path: str, extract_sections: bool = False
    ) -> Optional[str]:
        """
        Parse PDF dari file path dan ekstrak teks.

        Args:
            pdf_path: Path ke file PDF lokal
            extract_sections: Jika True, hanya extract sections spesifik.
                            Jika False, extract semua teks.

        Returns:
            Teks yang diekstrak dari PDF atau None jika gagal
        """
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file tidak ditemukan: {pdf_path}")
                return None

            full_text = self._extract_text_from_pdf(pdf_path)
            
            logger.info(f"Extracted {len(full_text)} characters from PDF")

            # Check if full_text is empty
            if not full_text or len(full_text.strip()) == 0:
                logger.error("PDF extraction resulted in empty text")
                return None

            # Jika extract_sections=True, parse sections dan gabungkan
            if extract_sections:
                sections = self.proposal_parser.parse_sections(full_text)
                sections_with_content = [s for s in sections.values() if s]
                
                logger.info(
                    f"Extracted sections from PDF. Total sections with content: {len(sections_with_content)}"
                )
                
                # Gabungkan sections
                text = self.proposal_parser.get_full_proposal_text(sections)
                
                # Fallback ke full text jika sections kosong
                if not text or len(text.strip()) < 100:
                    logger.warning(
                        f"Section extraction resulted in insufficient text ({len(text) if text else 0} chars). "
                        "Falling back to full PDF text."
                    )
                    text = full_text
            else:
                text = full_text

            return text

        except Exception as e:
            logger.error(f"Error parsing PDF file: {e}", exc_info=True)
            return None

    def parse_pdf_sections_from_file(self, pdf_path: str) -> Optional[Dict[str, str]]:
        """
        Parse PDF dari file path dan ekstrak sections terstruktur.

        Args:
            pdf_path: Path ke file PDF lokal

        Returns:
            Dictionary dengan section names dan texts, atau None jika gagal
        """
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file tidak ditemukan: {pdf_path}")
                return None

            full_text = self._extract_text_from_pdf(pdf_path)

            # Parse sections
            sections = self.proposal_parser.parse_sections(full_text)

            return sections

        except Exception as e:
            logger.error(f"Error parsing PDF sections: {e}", exc_info=True)
            return None


# Singleton instance
pdf_parser_service = PDFParserService()
