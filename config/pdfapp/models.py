from django.db import models

class PDFHistory(models.Model):

    operation_choices = [
        ('merge', 'Merge'),
        ('split', 'Split'),
        ('compress', 'Compress'),
        ('rotate', 'Rotate'),
    ]

    operation = models.CharField(max_length = 20, choices = operation_choices)

    output_file = models.FileField(upload_to='output/')

    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.operation
    