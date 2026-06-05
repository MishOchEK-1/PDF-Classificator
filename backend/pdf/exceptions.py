from rest_framework.exceptions import APIException


class PDFProcessingError(APIException):
    status_code = 422
    default_code = 'pdf_processing_error'
    default_detail = 'Unable to process the uploaded PDF.'


class CorruptedPDFError(PDFProcessingError):
    default_code = 'corrupted_pdf'
    default_detail = 'The uploaded PDF is corrupted or unreadable.'


class EmptyPDFError(PDFProcessingError):
    default_code = 'empty_pdf'
    default_detail = 'The uploaded PDF does not contain usable content.'


class ScannedPDFError(PDFProcessingError):
    default_code = 'scanned_pdf_without_text'
    default_detail = 'The uploaded PDF has no extractable text.'
