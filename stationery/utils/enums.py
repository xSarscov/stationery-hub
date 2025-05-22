from django.db import models

class DiscountTypeEnum(models.IntegerChoices):
    PERCENTAGE = 1, 'Percentage'
    FIXED_AMOUNT = 2, 'Fixed Amount'

class ScopeTypeEnum(models.IntegerChoices):
    ALL_PRODUCTS = 1, 'All products'
    SELECTED_PRODUCTS = 2, 'Specific products'
    ALL_CATEGORIES = 3, 'All categories'
    SELECTED_CATEGORIES = 4, 'Specific categories'

class MovementTypeEnum(models.TextChoices):
    IN = 'IN', 'Entrada'
    OUT = 'OUT', 'Salida'
    ADJUSTMENT = 'ADJ', 'Ajuste'

class MovementReasonEnum(models.TextChoices):
    PURCHASE = 'COMPRA', 'Compra a proveedor'
    SALE = 'VENTA', 'Venta a cliente'
    RETURN = 'DEVOLUCION', 'Devolución'
    ADJUSTMENT = 'AJUSTE', 'Ajuste de inventario'
    DAMAGED = 'DANADO', 'Mercancía dañada'
    EXPIRED = 'VENCIDO', 'Producto vencido'