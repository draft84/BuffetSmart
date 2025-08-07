from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from rest_framework.routers import DefaultRouter
from .views import (TraductorMasivoView, LoginView, OrganizationViewSet, UserViewSet, InstallView, LanguageViewSet, DishesViewSet, DishesLangViewSet, 
    DishesLangEditViewSet, AllergensViewSet, AllergenLangEditViewSet, RecipeViewSet, TimeViewSet, WeekViewSet, AssignmentViewSet, ExceptionViewSet, 
    SyncSolumLabelsView, SyncSolumTemplateView, LabelsScheduleView, MacListView, OnlyDishesViewSet, TokenView, MenuComplianceView, 
    ExceptionDetailsView, RestDishView, RestArticleView, GatewayView, GatewayView, LabelGatewayView, PatchGatewayView, HotelScheduleView, UpdateProductSolumView, 
    TotalExceptionAssignmentsView, SendEmailView, TimesScheduleView, ChangeHotelView, ListHotelView, TranslatePreviewViews, TranslateSavedViews, 
    CopyHorizontalAssignmentsView, DeleteExceptionView, CopyVerticalAssignmentsView, CopyExceptionView, start_scheduler, LabelsStatusViews, ListSchemaView, 
    ListTemplateView, AssignmentTemplateView, SchemasListView, UserListView, DeeplLanguagesView, 
    ExceptionMultipleView, HourZonetView, ExportExcelView, CreateMenuView, ExportDishesView, RestDishAssignmentView, MenuManagementViewSet, MenuAssignmentView, AssignFromTimeView,
    CopyHorizontalAssignmentsMagnamentView, CopyVerticalAssignmentsMagnamentView, DeleteMenuAssignmentView)

# Registrar rutas de la aplicación labels
from labels.views import RestaurantViewSet, LabelViewSet, TemplateViewSet

router = DefaultRouter()
router.register(r'organization', OrganizationViewSet)
router.register(r'user', UserViewSet)
router.register(r'languages', LanguageViewSet)
router.register(r'dishes', DishesViewSet)
router.register(r'only-dishes', OnlyDishesViewSet, basename='only-dishes')
router.register(r'disheslang', DishesLangViewSet)
# router.register(r'disheslang', DishesLangEditViewSet)
router.register(r'allergens', AllergensViewSet)
router.register(r'allergenslang', AllergenLangEditViewSet)
router.register(r'recipe', RecipeViewSet)
router.register(r'times', TimeViewSet)
router.register(r'weeks', WeekViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'menumagnament', MenuManagementViewSet)
router.register(r'exception', ExceptionViewSet)
router.register(r'restaurants', RestaurantViewSet)
router.register(r'labels', LabelViewSet)
router.register(r'template', TemplateViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('', TemplateView.as_view(template_name="home.html"), name="home"),
    path('install/', InstallView.as_view(), name="install"),
    path('list_template/', ListTemplateView.as_view(), name="list_template"),
    path('assignment_template/<int:template>/', AssignmentTemplateView.as_view(), name='assignment_template'),
    path('assignment_template/<int:template>/<str:mac>/', AssignmentTemplateView.as_view(), name='assignment_template'),
    path('mac_list/', MacListView.as_view(), name='mac_list'),
    path('sync_solum_label/<str:mac_address>/', SyncSolumLabelsView.as_view(), name='sync_solum_label'),
    path('restoredish_assignment/<int:day_of_week>/<str:articleId>/<int:dish_id>/<int:time_id>/', RestDishAssignmentView.as_view(), name='restoredish_assignment'),
    path('restoredish/<int:day_of_week>/<str:articleId>/<int:dish_id>/<int:time_id>/', RestDishView.as_view(), name='restoredish'),
    path('delete_exception/<int:day_of_week>/<str:articleId>/<int:dish_id>/<int:time_id>/', DeleteExceptionView.as_view(), name='delete_exception'),
    path('cleardish/<str:articleId>/', RestArticleView.as_view(), name='cleardish'),
    path('sync_solum_template/', SyncSolumTemplateView.as_view(), name='sync_solum_template'),
    path('token/', TokenView.as_view(), name='token'),
    path('labels_schedule/', LabelsScheduleView.as_view(), name='labels_schedule'),
    path('labels_schedule/<int:restaurant>/', LabelsScheduleView.as_view(), name='labels_schedule_whit_restaurant'),
    path('labels_status/<str:lbl_status>/', LabelsStatusViews.as_view(), name='labels_status'),
    path('languages_code/', DeeplLanguagesView.as_view(), name='languages_code'),
    path('start_scheduler/', start_scheduler, name='start_scheduler'),
    path('statistics/<str:start_date>/<str:end_date>/', MenuComplianceView.as_view(), name='statistics'),
    path('statistics/<str:start_date>/<str:end_date>/<str:turn>/', MenuComplianceView.as_view(), name='statistics_with_turn'),
    path('get_gateway/', GatewayView.as_view(), name='get_gateway'),
    path('send_email/', SendEmailView.as_view(), name='send_email'),
    path('regenerate_label/', LabelGatewayView.as_view(), name='regenerate_label'),
    path('reboot_gateway/<str:solum_gateway>/', PatchGatewayView.as_view(), name='reboot_gateway'),
    path('totalexception/<str:start_date>/<str:end_date>/', TotalExceptionAssignmentsView.as_view(), name='totalexception'),
    path('totalexception/<str:start_date>/<str:end_date>/<str:turn>/', TotalExceptionAssignmentsView.as_view(), name='totalexception_with_turn'),
    path('update_product_solum/<int:dish_id>/<int:label_id>/', UpdateProductSolumView.as_view(), name='update_product_solum'),
    path('listschemas/', ListSchemaView.as_view(), name='listhotel'),
    path('listhotel/', ListHotelView.as_view(), name='listhotel'),
    path('changehotel/<int:userID>/', ChangeHotelView.as_view(), name='changehotel'),
    path('cromexecute/<str:username>/<str:password>/', HotelScheduleView.as_view(), name='cromexecute'), # Para ejecutar los crom
    path('cromexecute/<str:username>/<str:password>/<int:restID>/', HotelScheduleView.as_view(), name='cromexecute'), # Para ejecutar los crom
    path('cromtime/<str:username>/<str:password>/', TimesScheduleView.as_view(), name='cromtime'),
    path('schemas_select/', SchemasListView.as_view(), name='schemas_select'),
    path('traductor/', TraductorMasivoView.as_view(), name='traductor'), 
    path('translations/<str:dish>/', TranslatePreviewViews.as_view(), name='tranlations'),
    path('translations_saved/', TranslateSavedViews.as_view(), name='translations_saved'),
    path('create_menu/', CreateMenuView.as_view(), name='create_menu'),
    path('user_list/', UserListView.as_view(), name='user_list'),
    path('copy-horizontal-assignments/<str:label_value>/', CopyHorizontalAssignmentsView.as_view(), name='update-horizontal-assignments'),
    path('copy-vertical-assignments/<int:day_value>/', CopyVerticalAssignmentsView.as_view(), name='update-vertical-assignments'),
    path('copy-horizontal-magnament/<str:label_value>/', CopyHorizontalAssignmentsMagnamentView.as_view(), name='update-horizontal-magnament'),
    path('copy-vertical-magnament/<int:day_value>/', CopyVerticalAssignmentsMagnamentView.as_view(), name='update-vertical-magnament'),
    path('copy-exceptions/', CopyExceptionView.as_view(), name='copy-exceptions'),
    path('multiple_exception/', ExceptionMultipleView.as_view(), name='multiple_exception'),
    path('hour_zone/', HourZonetView.as_view(), name='hour_zone'),
    path('export_excel/<int:week_id>/', ExportExcelView.as_view(), name='export_excel'),
    path('export_dishes/', ExportDishesView.as_view(), name='dishes-export-excel'),
    path('menu_assignments/', MenuAssignmentView.as_view(), name='menu_assignments'),
    path('assignments_time/', AssignFromTimeView.as_view(), name='assignments_time'),
    path('delete_magnament_assignment/<int:restaurant_id>/', DeleteMenuAssignmentView.as_view(), name='delete_magnament_assignment'),
]
