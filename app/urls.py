from rest_framework.routers import DefaultRouter

from .views import (
    EstacionamentoViewSet,
    FiscalViewSet,
    MultaViewSet,
    PagamentoViewSet,
    UsuarioViewSet,
    VagaViewSet,
    VeiculoViewSet,
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'veiculos', VeiculoViewSet)
router.register(r'vagas', VagaViewSet)
router.register(r'estacionamentos', EstacionamentoViewSet)
router.register(r'pagamentos', PagamentoViewSet)
router.register(r'fiscais', FiscalViewSet)
router.register(r'multas', MultaViewSet)

urlpatterns = router.urls
