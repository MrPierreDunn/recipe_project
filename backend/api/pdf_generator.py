import io
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from recipes.models import IngredientRecipe

CART_TITLE = 'СПИСОК ПОКУПОК'
EMPTY_CART_TITLE = 'Список покупок пуст'
FONTS_DIR = Path('./static/fonts/DejaVuSerif.ttf').resolve()


def download_pdf_shopping_cart(user, ingredients_list):
    buffer = io.BytesIO()
    pdf_page = canvas.Canvas(buffer, pagesize=letter)

    pdfmetrics.registerFont(TTFont('DejaVuSerif', FONTS_DIR))
    pdf_page.setFont('DejaVuSerif', 14)

    x_value, y_value = 20, 635

    if ingredients_list:
        pdf_page.drawCentredString(315, 700, CART_TITLE)

        for value in ingredients_list:
            name = value['ingredient__name'].capitalize()
            amount = value['total_amount']
            measure = value['ingredient__measurement_unit']
            write_string = f'{name} - {amount} ({measure});'
            pdf_page.drawString(
                x_value, y_value, write_string
            )
            y_value -= 30
        pdf_page.save()
        buffer.seek(0)
        return buffer

    pdf_page.drawCentredString(315, 425, EMPTY_CART_TITLE)
    pdf_page.showPage()
    pdf_page.save()
    buffer.seek(0)
    return buffer
