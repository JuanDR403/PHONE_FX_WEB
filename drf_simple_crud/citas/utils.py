def tiene_permiso(request, roles_permitidos):
    """
    Función auxiliar para verificar permisos basados en roles
    """
    if not request.user.is_authenticated:
        return False

    perfil = getattr(request.user, 'perfil_usuarios', None)
    if perfil and perfil.id_rol and perfil.id_rol.nombre:
        rol_actual = perfil.id_rol.nombre.lower()
        return rol_actual in [r.lower() for r in roles_permitidos]
    return False


def obtener_rol_usuario(request):
    """
    Obtiene el nombre del rol del usuario actual
    """
    if not request.user.is_authenticated:
        return None

    perfil = getattr(request.user, 'perfil_usuarios', None)
    if perfil and perfil.id_rol and perfil.id_rol.nombre:
        return perfil.id_rol.nombre.lower()
    return None