from django import forms
from django.core.exceptions import ValidationError

from catalog.models import Product

FORBIDDEN_WORDS = (
    "казино",
    "криптовалюта",
    "крипта",
    "биржа",
    "дешево",
    "бесплатно",
    "обман",
    "полиция",
    "радар",
)

ALLOWED_IMAGE_TYPES = (
    "image/jpeg",
    "image/png",
)

MAX_IMAGE_SIZE = 5 * 1024 * 1024


class ProductForm(forms.ModelForm):
    """Форма создания и изменения товара."""

    price = forms.IntegerField(
        label="Цена за покупку",
    )

    class Meta:
        model = Product
        fields = (
            "name",
            "description",
            "image",
            "category",
            "price",
        )

    def __init__(self, *args, **kwargs):
        """Добавляет полям формы классы Bootstrap."""
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    "class": "form-check-input",
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    "class": "form-select",
                })
            else:
                field.widget.attrs.update({
                    "class": "form-control",
                })

    def clean_name(self):
        """Запрещает нежелательные слова в названии товара."""
        name = self.cleaned_data.get("name", "")

        for word in FORBIDDEN_WORDS:
            if word in name.lower():
                raise ValidationError(
                    f"В названии нельзя использовать слово «{word}»."
                )
        return name

    def clean_description(self):
        """Запрещает нежелательные слова в описании товара."""
        description = self.cleaned_data.get("description") or ""

        for word in FORBIDDEN_WORDS:
            if word in description.lower():
                raise ValidationError(
                    f"В описании нельзя использовать слово «{word}»."
                )

        return description

    def clean_price(self):
        """Запрещает отрицательную цену товара."""
        price = self.cleaned_data.get("price")

        if price is not None and price < 0:
            raise ValidationError(
                "Цена товара не может быть отрицательной."
            )

        return price

    def clean_image(self):
        """Проверяет формат и размер изображения товара."""
        image = self.cleaned_data.get("image")

        if not image:
            return image

        if image.size > MAX_IMAGE_SIZE:
            raise ValidationError(
                "Размер изображения не должен превышать 5 МБ."
            )

        if (
            hasattr(image, "content_type")
            and image.content_type not in ALLOWED_IMAGE_TYPES
        ):
            raise ValidationError(
                "Разрешены только изображения JPEG и PNG."
            )

        return image
