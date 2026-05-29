from django.contrib import admin
from .models import Restaurant,TableType,Menu,MenuItem,Reservation,ReservationGuests
# Register your models here.
class TableTypeInline(admin.TabularInline):
    model=TableType
    extra=0
class MenuInline(admin.TabularInline):
    model=Menu
    extra=0
    
class MenuItemInline(admin.TabularInline):
    model=MenuItem
    extra=0
    
class ReservationGuestsInline(admin.TabularInline):
    model=ReservationGuests
    extra=0

class ReservationInline(admin.TabularInline):
    model=Reservation
    extra=0

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    inlines=[TableTypeInline,MenuInline]
    

@admin.register(TableType)
class TableTypeAdmin(admin.ModelAdmin):
    inlines=[ReservationInline]
    list_filter=[
        "name",
        "type"
    ]

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    inlines=[MenuItemInline]

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    inlines=[ReservationGuestsInline]
    list_filter = [
        "starts_at",
        "status"
    ]
    
@admin.register(ReservationGuests)
class ReservationGuestsAdmin(admin.ModelAdmin):
    pass