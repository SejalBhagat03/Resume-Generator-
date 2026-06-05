from abc import ABC, abstractmethod

class BaseTemplate(ABC):
    @abstractmethod
    def generate(self, data, pdf_filename, accent_color, font_scale, margin_size, spacing_scale=1.0, padding_scale=1.0, layout_locked=False, **kwargs):
        """
        Compiles the resume data into a ReportLab PDF.
        
        Args:
            data (dict): The resume data conforming to schema.json
            pdf_filename (str): Path to write the PDF file to
            accent_color (str): Hex color code for style accentuation (e.g. #2563EB)
            font_scale (float): Multiplier to scale overall fonts and spacing
            margin_size (float): The default top/bottom page margin in points
            
        Returns:
            (bool, str): A tuple containing (success_status, warning_or_error_msg)
        """
        pass
