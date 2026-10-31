from django.contrib import admin
from .models import PDFHistory


@admin.register(PDFHistory)
class PDFHistoryAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'operation',
        'created_at'
    )

    list_filter = ('operation', 'created_at')