# 🎉 Usuario Confirmado - Guía de Uso

## ✅ Usuario Listo para Login

**Email confirmado**: `carlosm@mail.com`  
**Estado**: ✅ Activo y confirmado

## 🚀 Cómo Hacer Login

1. Abre el navegador: http://localhost:5173
2. Serás redirigido a la página de login
3. Ingresa:
   - **Email**: `carlosm@mail.com`
   - **Password**: (la contraseña que usaste al registrarte)
4. Click en "Sign In"

## 📝 Crear Nuevos Usuarios

### Opción 1: Desde la Interfaz Web
1. Ve a http://localhost:5173/signup
2. Completa el formulario
3. El usuario será creado pero **requerirá confirmación**

### Opción 2: Confirmar Usuario Automáticamente

Después de crear un usuario en signup, corre este comando:

```bash
cd backend
PYTHONPATH=$(pwd) python3 confirm_user.py nuevo_email@mail.com
```

## 🔧 Desactivar Confirmación de Email (Recomendado para MVP)

Para que los nuevos usuarios puedan hacer login inmediatamente sin confirmación:

1. Ve al Dashboard de Supabase: https://supabase.com/dashboard/project/vqcjovttaucekugwmefj
2. Navega a: **Authentication** → **Providers** → **Email**
3. Desactiva **"Confirm email"**
4. Guarda los cambios

Después de esto, todos los nuevos usuarios podrán hacer login inmediatamente.

## 🧪 Usuarios de Prueba Disponibles

Ya confirmados y listos para usar:

| Email | Uso |
|-------|-----|
| admin@local.test | Usuario administrador |
| ops1@local.test | Operador 1 |
| ops2@local.test | Operador 2 |
| reviewer@local.test | Revisor |
| readonly@local.test | Solo lectura |
| **carlosm@mail.com** | **Tu usuario (recién confirmado)** |

**Nota**: Estos usuarios de prueba fueron creados con el script de sincronización y no tienen contraseñas reales configuradas en modo production. Para modo production real, usa carlosm@mail.com o crea nuevos usuarios.

## 🔍 Verificar Estado de Usuarios

Para ver todos los usuarios y su estado:

```bash
cd backend
PYTHONPATH=$(pwd) python3 test_auth.py
```

Esto mostrará:
- ✅ Usuarios confirmados (pueden hacer login)
- ⚠️ Usuarios pendientes (necesitan confirmación)

## 🛠️ Scripts Útiles

### Confirmar Usuario
```bash
python3 confirm_user.py email@example.com
```

### Ver Estado de Auth
```bash
python3 test_auth.py
```

## 📋 Flujo Completo de Usuario Nuevo

1. **Signup**: Usuario se registra en `/signup`
2. **Confirmación Email**: 
   - Opción A: Recibe email y hace click en link
   - Opción B: Admin confirma manualmente con script
   - Opción C: Desactivas confirmación en dashboard
3. **Login**: Usuario hace login en `/login`
4. **Dashboard**: Accede a `/clients` y ve los 10 clientes sincronizados

## 🎯 Estado Actual del Sistema

✅ Backend corriendo: http://localhost:8000  
✅ Frontend corriendo: http://localhost:5173  
✅ Supabase conectado: vqcjovttaucekugwmefj.supabase.co  
✅ 10 clientes sincronizados  
✅ 118 conversaciones  
✅ 21 documentos PDF  
✅ 6 usuarios en Auth (5 de prueba + carlosm@mail.com)

## 💡 Próximos Pasos Recomendados

1. **Probar Login**: Inicia sesión con carlosm@mail.com
2. **Navegar Clientes**: Ve los 10 clientes en el dashboard
3. **Descargar PDFs**: Abre un cliente y descarga documentos
4. **Desactivar Confirmación Email**: Para agilizar registro de nuevos usuarios
5. **Crear Más Usuarios**: Para simular diferentes roles

## 🐛 Troubleshooting

### No puedo hacer login
- Verifica que el usuario esté confirmado: `python3 test_auth.py`
- Confirma manualmente: `python3 confirm_user.py tu_email@mail.com`
- Verifica que ingresaste la contraseña correcta

### El signup no funciona
- Verifica que `VITE_APP_MODE=real` en `frontend/.env`
- Verifica que las credenciales de Supabase estén correctas
- Revisa la consola del navegador (F12) para ver errores

### Los PDFs no se descargan
- Verifica que el backend esté corriendo: http://localhost:8000/health
- Los PDFs están en modo público: https://vqcjovttaucekugwmefj.supabase.co/storage/v1/object/public/client-documents/

---

**¿Necesitas ayuda?** Todos los scripts están en la carpeta `backend/`:
- `test_auth.py` - Ver usuarios
- `confirm_user.py` - Confirmar emails
- `sync_to_supabase.sh` - Re-sincronizar datos
