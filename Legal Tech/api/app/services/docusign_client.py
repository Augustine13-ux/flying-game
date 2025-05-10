from docusign_esign import EnvelopeDefinition, Document, Signer, SignHere, Tabs, EnvelopesApi
from docusign_esign.client.api_client import ApiClient
from typing import List, Dict
import os
from .signature_detector import SignatureDetector

class DocuSignClient:
    def __init__(self, account_id: str, access_token: str, base_path: str):
        """Initialize DocuSign client with account credentials."""
        self.account_id = account_id
        self.api_client = ApiClient()
        self.api_client.host = base_path
        self.api_client.set_default_header("Authorization", f"Bearer {access_token}")
        self.envelopes_api = EnvelopesApi(self.api_client)

    def create_envelope(
        self,
        subject: str,
        pdf_path: str,
        recipients: List[Dict[str, str]]
    ) -> str:
        """
        Create a DocuSign envelope with signature tabs placed at detected signature locations.
        
        Args:
            subject: Email subject for the envelope
            pdf_path: Path to the PDF document
            recipients: List of recipient dictionaries with name, email, role, and page_no
            
        Returns:
            str: The created envelope ID
        """
        # Read the PDF file
        with open(pdf_path, 'rb') as file:
            pdf_bytes = file.read()

        # Create document object
        document = Document(
            document_base64=pdf_bytes,
            name=os.path.basename(pdf_path),
            file_extension='pdf',
            document_id='1'
        )

        # Initialize signature detector
        signature_detector = SignatureDetector(pdf_path)

        # Create signers with signature tabs
        signers = []
        for recipient in recipients:
            # Get signature coordinates for the specified page
            signature_coords = signature_detector.detect_signature(recipient['page_no'])
            
            if not signature_coords:
                raise ValueError(f"No signature location found on page {recipient['page_no']}")

            # Create sign here tab
            sign_here = SignHere(
                anchor_string="Signature",
                anchor_units="pixels",
                anchor_x_offset=str(signature_coords['x']),
                anchor_y_offset=str(signature_coords['y']),
                page_number=str(recipient['page_no'])
            )

            # Create tabs object
            tabs = Tabs(sign_here_tabs=[sign_here])

            # Create signer
            signer = Signer(
                email=recipient['email'],
                name=recipient['name'],
                recipient_id=str(len(signers) + 1),
                routing_order=str(len(signers) + 1),
                tabs=tabs
            )
            signers.append(signer)

        # Create envelope definition
        envelope_definition = EnvelopeDefinition(
            email_subject=subject,
            documents=[document],
            recipients={"signers": signers},
            status="sent"
        )

        # Create the envelope
        envelope_summary = self.envelopes_api.create_envelope(
            account_id=self.account_id,
            envelope_definition=envelope_definition
        )

        return envelope_summary.envelope_id 