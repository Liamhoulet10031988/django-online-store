"""Общие примеси для Django-форм проекта."""

from django import forms


class FormStyleMixin:
    """Добавляет полям формы Bootstrap-классы."""

    def __init__(self, *args, **kwargs):
        """Настраивает CSS-класс каждого виджета формы."""
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
