
import os
from io import BytesIO

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from pypdf import PdfReader, PdfWriter
import pikepdf

from .models import PDFHistory


MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TOTAL_SIZE = 30 * 1024 * 1024
MAX_PAGES = 500


def home(request):
    return render(request, 'pdfapp/index.html')


def validate_pdf(pdf):

    if not pdf.name.lower().endswith('.pdf'):
        raise ValueError('Only PDF files are allowed.')

    if pdf.size > MAX_FILE_SIZE:
        raise ValueError(f'{pdf.name} exceeds the 10 MB limit.')

    data = pdf.read()
    pdf.seek(0)

    reader = PdfReader(BytesIO(data), strict=True)

    if reader.is_encrypted:
        raise ValueError(f'{pdf.name} is password protected.')

    if len(reader.pages) == 0:
        raise ValueError(f'{pdf.name} has no pages.')

    return data, reader


def save_output(operation, output_data):

    filename = f'{operation}_{PDFHistory.objects.count() + 1}.pdf'

    history = PDFHistory(operation=operation)

    history.output_file.save(
        filename,
        ContentFile(output_data),
        save=True
    )

    return history


@require_POST
@csrf_protect
def process_pdf(request):

    operation = request.POST.get('operation')

    allowed_operations = ['merge', 'split', 'compress', 'rotate']

    if operation not in allowed_operations:
        return JsonResponse({
            'success': False,
            'error': 'Invalid operation.'
        }, status=400)

    files = request.FILES.getlist('pdf_files')

    if not files:
        return JsonResponse({
            'success': False,
            'error': 'Please upload PDF files.'
        }, status=400)

    if len(files) > 10:
        return JsonResponse({
            'success': False,
            'error': 'Maximum 10 PDF files allowed.'
        }, status=400)

    if sum(f.size for f in files) > MAX_TOTAL_SIZE:
        return JsonResponse({
            'success': False,
            'error': 'Total upload size cannot exceed 30 MB.'
        }, status=400)

    try:

        if operation == 'merge' and len(files) < 2:
            raise ValueError('Select at least 2 PDF files to merge.')

        if operation != 'merge' and len(files) != 1:
            raise ValueError('Select exactly 1 PDF file.')

        pdf_data = []

        for pdf in files:
            data, reader = validate_pdf(pdf)
            pdf_data.append((data, reader))

        total_pages = sum(
            len(reader.pages) for data, reader in pdf_data
        )

        if total_pages > MAX_PAGES:
            raise ValueError('Maximum 500 pages allowed.')

        output = BytesIO()

        # 1. MERGE PDF
        if operation == 'merge':

            writer = PdfWriter()

            try:
                for data, reader in pdf_data:
                    writer.append(reader)

                writer.write(output)

            finally:
                writer.close()

        # 2. SPLIT PDF
        elif operation == 'split':

            data, reader = pdf_data[0]

            page_range = request.POST.get('page_range', '').strip()

            if not page_range:
                raise ValueError('Enter page numbers or ranges.')

            selected_pages = set()

            try:
                for part in page_range.split(','):

                    part = part.strip()

                    if '-' in part:
                        start, end = map(int, part.split('-', 1))

                        if start > end:
                            raise ValueError()

                        pages = range(start, end + 1)

                    else:
                        pages = [int(part)]

                    for page in pages:

                        if page < 1 or page > len(reader.pages):
                            raise ValueError()

                        selected_pages.add(page - 1)

            except (ValueError, TypeError):
                raise ValueError(
                    'Invalid page range. Example: 1-3,5'
                )

            writer = PdfWriter()

            try:
                for page in sorted(selected_pages):
                    writer.add_page(reader.pages[page])

                writer.write(output)

            finally:
                writer.close()

        # 3. COMPRESS PDF
        elif operation == 'compress':

            data, reader = pdf_data[0]

            with pikepdf.open(BytesIO(data)) as pdf:

                pdf.save(
                    output,
                    compress_streams=True,
                    recompress_flate=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate
                )

        # 4. ROTATE PDF
        elif operation == 'rotate':

            data, reader = pdf_data[0]

            degrees = int(request.POST.get('degrees', '90'))

            if degrees not in [90, 180, 270]:
                raise ValueError('Choose 90, 180 or 270 degrees.')

            writer = PdfWriter()

            try:
                writer.append(reader)

                for page in writer.pages:
                    page.rotate(degrees)

                writer.write(output)

            finally:
                writer.close()

        output_data = output.getvalue()

        if not output_data:
            raise ValueError('PDF processing failed.')

        history = save_output(operation, output_data)

        return JsonResponse({
            'success': True,
            'message': 'PDF processed successfully!',
            'download_url': history.output_file.url,
            'filename': os.path.basename(history.output_file.name),
            'size': len(output_data)
        })

    except ValueError as e:

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception:

        return JsonResponse({
            'success': False,
            'error': 'Unable to process this PDF. Check the file and try again.'
        }, status=400)


def history(request):

    records = PDFHistory.objects.order_by('-created_at')[:20]

    return render(request, 'pdfapp/history.html', {
        'records': records
    })

