from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from decimal import Decimal
from django.contrib.postgres.indexes import GinIndex
from jsonschema import validate, ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Q, CheckConstraint, Sum
from .utils.enums import DiscountTypeEnum, ScopeTypeEnum, MovementReasonEnum, MovementTypeEnum

def default_product_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {},
        "required": []
    }

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    product_schema = models.JSONField(default={"$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {},
        "required": []}, blank=True,)

    class Meta: 
        verbose_name_plural='Categories'

    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta: 
        verbose_name_plural='Companies'

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=255, blank=True, null=True, unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    brands = models.ManyToManyField('Brand')
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'{self.name} - {self.company}'

class Product(models.Model):
    name = models.CharField(max_length=100)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    minimum_stock = models.IntegerField()
    stock = models.IntegerField()
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    suppliers = models.ManyToManyField(Supplier, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    active = models.BooleanField(default=True)
    brand = models.ForeignKey('Brand', on_delete=models.PROTECT, related_name='products', blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Atributos específicos según el tipo de producto"
    )

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['stock']),
            GinIndex(fields=['attributes'], name='gin_attributes')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(stock__gte=0),
                name='non_negative_stock'
            )
        ]

    def clean(self):
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative")
        if self.sale_price < self.purchase_price:
            raise ValidationError("Sale price cannot be lower than purchase price")
        
        if self.category and self.category.product_schema:
            try:
                validate(instance=self.attributes, schema=self.category.product_schema)
            except ValidationError as e:
                raise ValidationError({'attributes': f"Datos inválidos: {e.message}"})

        
    def check_stock(self, required_quantity):
        return self.stock >= required_quantity
    
    def get_attribute(self, key, default=None):
        return self.attributes.get(key, default)
    
    def update_attributes(self, new_attributes):
        self.attributes.update(new_attributes)
        self.save(update_fields=['attributes'])

    def __str__(self):
        return self.name
    
class InvoiceBase(models.Model):
    # id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date      = models.DateTimeField(auto_now_add=True)
    due_date        = models.DateField()
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    discount        = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], blank=True, null=True)
    total_amount    = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    notes           = models.TextField(blank=True, null=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    last_updated    = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True
        constraints = [
            CheckConstraint(
                check=Q(due_date__gte=F('issue_date')),
                name='%(app_label)s_%(class)s_due_after_issue'
            ),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
class TransactionStatus(models.Model):
    code  = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label

class Purchase(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    invoice_image = models.ImageField(upload_to='purchases/invoices/', blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    status = models.ForeignKey(TransactionStatus, on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)
    invoice_number = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="Número de Factura"
    )
    payment_method = models.ForeignKey(
        'PaymentMethod',
        to_field='code',
        db_column='payment_method',
        on_delete=models.PROTECT,
        help_text="Método de pago usado para la compra",
        null=True,
        blank=True,
        default='CA'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True) 
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def clean(self):
        if self.total < 0:
            ValidationError("Total cannot be negative")

    def __str__(self):
        return f"Purchase {self.id} - {self.date}"

class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_attributes = models.JSONField(
        default=dict,
        help_text="Atributos del producto al momento de la compra"
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and self.product:
            self.purchase_attributes = self.product.attributes.copy()

        self.product.stock = F('stock') + self.quantity
        self.product.purchase_price = self.unit_price
        self.product.save()

        super().save(*args, **kwargs)

        if is_new:
            in_type = MovementType.objects.get(code='IN')
            StockMovement.objects.create(
                product        = self.product,
                quantity       = self.quantity,
                movement_type  = in_type,
                reason         = MovementReasonEnum.PURCHASE,
                purchase       = self.purchase,
                created_by     = self.purchase.created_by
            )

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"

class Customer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True, unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.name
    
class DiscountType(models.Model):
    code  = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=50)
    active= models.BooleanField(default=True)

    def __str__(self):
        return self.label
    
class ScopeType(models.Model):
    code  = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=50)                
    active= models.BooleanField(default=True)

    def __str__(self):
        return self.label

class Discount(models.Model):

    name = models.CharField(max_length=100)
    type = models.ForeignKey(
        DiscountType,
        on_delete=models.PROTECT
    )
    value = models.DecimalField(max_digits=10, decimal_places=2)
    scope = models.ForeignKey(
        ScopeType,
        on_delete=models.PROTECT
    )
    products = models.ManyToManyField(Product, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    active = models.BooleanField(
        default=True,
        help_text="Discount available to apply"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        if self.scope == ScopeTypeEnum.SELECTED_PRODUCTS and not self.products.exists():
            raise ValidationError("You must select at least one product for this scope")
            
        if self.scope == ScopeTypeEnum.SELECTED_CATEGORIES and not self.categories.exists():
            raise ValidationError("You must select at least one category for this scope")

    def applicable_products(self):
        """Returns queryset with products eligible for discount"""
        if self.scope == ScopeTypeEnum.ALL_PRODUCTS:
            return Product.objects.all()
        
        if self.scope == ScopeTypeEnum.ALL_CATEGORIES:
            return Product.objects.filter(category__isnull=False)
        
        if self.scope == ScopeTypeEnum.SELECTED_CATEGORIES:
            return Product.objects.filter(category__in=self.categories.all())
        
        return self.products.all()

    def apply_to_product(self, product):
        """Checks if discount applies to a specific product"""
        if not self.active:
            return False
            
        if self.scope == ScopeTypeEnum.ALL_PRODUCTS:
            return True
            
        if self.scope == ScopeTypeEnum.ALL_CATEGORIES and product.category:
            return True
            
        if self.scope == ScopeTypeEnum.SELECTED_CATEGORIES:
            return product.category in self.categories.all()
            
        return product in self.products.all()

    def calculate_discount(self, original_price):
        if not self.is_active:
            return 0
            
        if self.type == DiscountTypeEnum.PERCENTAGE:
            return original_price * (self.value / 100)
            
        return min(self.value, original_price)    
class PaymentMethod(models.Model):
    code        = models.CharField(max_length=2, unique=True, primary_key=True)
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    active      = models.BooleanField(default=True)
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    last_updated= models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.name

class Sale(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.ForeignKey(PaymentMethod, to_field='code', db_column='payment_method', on_delete=models.PROTECT)
    status = models.ForeignKey(TransactionStatus, on_delete=models.PROTECT)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='SaleDetail')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date', 'customer']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Sale {self.id} - {self.date}"

class SaleDetail(models.Model):
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_name = models.CharField(max_length=100, blank=True, null=True)
    discount_type = models.PositiveIntegerField(choices=DiscountTypeEnum.choices, blank=True, null=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    sale_attributes = models.JSONField(
        default=dict,
        help_text="Atributos del producto al momento de la venta"
    )

    @property
    def final_price(self):
        if self.discount_type == DiscountTypeEnum.PERCENTAGE:
            return self.unit_price * (1 - self.discount_value/100)
        elif self.discount_type == DiscountTypeEnum.FIXED_AMOUNT:
            return max(self.unit_price - self.discount_value, Decimal('0'))
        return self.unit_price



    def clean(self):
        try:
            product = Product.objects.get(pk=self.product_id)
            if not product.active:
                raise ValidationError("No se puede vender un producto inactivo")
        except ObjectDoesNotExist:
                raise ValidationError("Producto asociado no existe")

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and self.product:
            self.sale_attributes = self.product.attributes.copy()

        self.product.stock = F('stock') - self.quantity
        self.product.save()

        super().save(*args, **kwargs)

        if is_new:
            out_type = MovementType.objects.get(code='OUT')
            StockMovement.objects.create(
                product       = self.product,
                quantity      = self.quantity,
                movement_type = out_type,
                reason        = MovementReasonEnum.SALE,
                sale          = self.sale,
                created_by    = self.created_by
            )

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units from {self.sale}"

class SaleInvoice(InvoiceBase):
    sale = models.OneToOneField(
        'Sale',
        on_delete=models.CASCADE,
        related_name='invoice'
    )

class PurchaseInvoice(InvoiceBase):
    purchase = models.OneToOneField(
        'Purchase',
        on_delete=models.CASCADE,
        related_name='invoice'
    )

class MovementType(models.Model):
    code   = models.CharField(max_length=10, unique=True)  
    label  = models.CharField(max_length=50)               
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.label

class StockMovement(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Número de unidades movidas (debe ser ≥ 1)")
    reason = models.CharField(max_length=15, choices=MovementReasonEnum.choices, blank=True, null=True)
    movement_type = models.ForeignKey(MovementType, on_delete=models.PROTECT, related_name='stock_movements')
    date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements_created')

    purchase = models.ForeignKey(
        'Purchase', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stock_movements'
    )
    
    sale = models.ForeignKey(
        'Sale', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stock_movements'
    )
    
    purchase_return = models.ForeignKey(
        'PurchaseReturn', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stock_movements'
    )
    
    sale_return = models.ForeignKey(
        'SaleReturn', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stock_movements'
    )


    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['movement_type']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(
                    (Q(purchase__isnull=True) & Q(sale__isnull=True) & Q(purchase_return__isnull=True) & Q(sale_return__isnull=True)) |
                    (Q(purchase__isnull=False) & Q(sale__isnull=True) & Q(purchase_return__isnull=True) & Q(sale_return__isnull=True)) |
                    (Q(purchase__isnull=True) & Q(sale__isnull=False) & Q(purchase_return__isnull=True) & Q(sale_return__isnull=True)) |
                    (Q(purchase__isnull=True) & Q(sale__isnull=True) & Q(purchase_return__isnull=False) & Q(sale_return__isnull=True)) |
                    (Q(purchase__isnull=True) & Q(sale__isnull=True) & Q(purchase_return__isnull=True) & Q(sale_return__isnull=False))
                ),
                name='single_transaction_per_movement'
            )
        ]

    # def clean(self):
    #     code = self.movement_type.code
    #     if code == 'IN' and self.reason not in [
    #         self.MovementReason.PURCHASE,
    #         self.MovementReason.RETURN,
    #         self.MovementReason.ADJUSTMENT
    #     ]:
    #         raise ValidationError("Razón inválida para entrada de stock")

    #     if code == 'OUT' and self.reason not in [
    #         self.MovementReason.SALE,
    #         self.MovementReason.RETURN,
    #         self.MovementReason.DAMAGED,
    #         self.MovementReason.EXPIRED,
    #         self.MovementReason.ADJUSTMENT
    #     ]:
    #         raise ValidationError("Razón inválida para salida de stock")

    def __str__(self):
        return f"{self.movement_type} of {self.quantity} units of {self.product.name}"

class PurchaseReturn(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    reason = models.TextField()
    date = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(TransactionStatus, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.quantity > self.purchase.purchasedetail_set.get(product=self.product).quantity:
            raise ValidationError("Return quantity exceeds original purchase")
            
        super().save(*args, **kwargs)
        
        if self.status == 'APPROVED':
            self.product.stock = F('stock') - self.quantity
            self.product.save()
            
            StockMovement.objects.create(
                product=self.product,
                quantity=self.quantity,
                movement_type='Out',
                purchase_return=self
            )

class SaleReturn(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    reason = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ], default='PENDING')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        original_detail = self.sale.saledetail_set.get(product=self.product)
        if self.quantity > original_detail.quantity:
            raise ValidationError("Return quantity exceeds original sale")
        
        super().save(*args, **kwargs)
        
        if self.status == 'APPROVED':
            self.product.stock = F('stock') + self.quantity
            self.product.save()
            
            StockMovement.objects.create(
                product=self.product,
                quantity=self.quantity,
                movement_type='In',
                sale_return=self
            )

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    creation_date = models.DateField(auto_now_add=True)
    image = models.ImageField(upload_to='brands/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_brand_name')
        ]

    def __str__(self):
        return f"Brand {self.name}"